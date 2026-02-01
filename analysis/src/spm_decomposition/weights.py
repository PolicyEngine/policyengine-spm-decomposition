"""Weight rebalancing analysis: how Enhanced CPS re-weighting shifts child poverty."""

import numpy as np

from .config import INCOME_QUINTILE_LABELS, FAMILY_STRUCTURE_LABELS
from .poverty import _map_spm_to_person


def _weighted_quantiles(values, weights, quantiles):
    """Compute weighted quantiles."""
    sorted_idx = np.argsort(values)
    sorted_vals = values[sorted_idx]
    sorted_weights = weights[sorted_idx]
    cumulative = np.cumsum(sorted_weights)
    total = cumulative[-1]
    return np.interp(
        [q * total for q in quantiles],
        cumulative,
        sorted_vals,
    )


def _assign_quintile(values, weights):
    """Assign each observation to an income quintile (0-4)."""
    breakpoints = _weighted_quantiles(values, weights, [0.2, 0.4, 0.6, 0.8])
    quintile = np.zeros(len(values), dtype=int)
    for i, bp in enumerate(breakpoints):
        quintile[values > bp] = i + 1
    return quintile


def _get_person_level_grouping(sim, period):
    """Get income quintiles and family structure at person level.

    Maps SPM-unit income and tax-unit joint status to person level.
    """
    # Income: SPM-unit level → person level
    spm_income = sim.calc("spm_unit_net_income_reported", period=period)
    person_income = _map_spm_to_person(sim, spm_income.values, period)

    # Weights at person level
    person_weight = sim.calc("person_weight", period=period).values

    # Quintiles based on person-level income (with person weights)
    quintiles = _assign_quintile(person_income, person_weight)

    # Family structure: tax_unit_is_joint → map to person level
    # tax_unit_is_joint is at tax_unit level
    tax_unit_id = sim.calc("tax_unit_id", period=period).values
    person_tax_unit_id = sim.calc("person_tax_unit_id", period=period).values
    joint_values = sim.calc("tax_unit_is_joint", period=period).values.astype(float)
    tu_id_to_idx = {int(tid): i for i, tid in enumerate(tax_unit_id)}
    family_is_joint = np.array([joint_values[tu_id_to_idx[int(pid)]] for pid in person_tax_unit_id])

    return quintiles, family_is_joint, person_weight


def _compute_group_stats(sim, quintiles, family_is_joint, person_weight, period):
    """Compute per-group child poverty rate and child share for one simulation."""
    is_child = sim.calc("is_child", period=period).values
    person_in_poverty = sim.calc("person_in_poverty", period=period).values
    child_mask = is_child == 1

    total_children_weighted = float(np.sum(person_weight[child_mask]))
    groups = []

    for q_idx, q_label in enumerate(INCOME_QUINTILE_LABELS):
        for fs_idx, fs_label in enumerate(FAMILY_STRUCTURE_LABELS):
            is_joint_val = float(fs_idx)  # 0 = single parent, 1 = married
            mask = (
                child_mask
                & (quintiles == q_idx)
                & (family_is_joint == is_joint_val)
            )
            weighted_children = float(np.sum(person_weight[mask]))
            if weighted_children > 0:
                poverty_rate = float(
                    np.average(person_in_poverty[mask], weights=person_weight[mask])
                )
            else:
                poverty_rate = 0.0

            child_share = (
                weighted_children / total_children_weighted
                if total_children_weighted > 0
                else 0.0
            )
            groups.append(
                {
                    "label": f"{q_label} / {fs_label}",
                    "poverty_rate": poverty_rate,
                    "child_share": child_share,
                }
            )

    return groups


def compute_weight_rebalancing(raw_sim, enhanced_sim, period=2024) -> dict:
    """Compare child poverty across income quintile x family structure groups.

    Parameters
    ----------
    raw_sim : Microsimulation
        Raw CPS microsimulation.
    enhanced_sim : Microsimulation
        Enhanced CPS microsimulation (PUF-imputed, re-weighted).
    period : int
        Tax year.

    Returns
    -------
    dict
        ``{"groups": [{"label", "raw_cps_poverty_rate", "enhanced_cps_poverty_rate",
        "raw_cps_child_share", "enhanced_cps_child_share"}, ...]}``
    """
    raw_quintiles, raw_joint, raw_pw = _get_person_level_grouping(raw_sim, period)
    enh_quintiles, enh_joint, enh_pw = _get_person_level_grouping(enhanced_sim, period)

    raw_groups = _compute_group_stats(raw_sim, raw_quintiles, raw_joint, raw_pw, period)
    enh_groups = _compute_group_stats(enhanced_sim, enh_quintiles, enh_joint, enh_pw, period)

    # Merge raw and enhanced results by label
    merged = []
    for rg, eg in zip(raw_groups, enh_groups):
        assert rg["label"] == eg["label"]
        merged.append(
            {
                "label": rg["label"],
                "raw_cps_poverty_rate": rg["poverty_rate"],
                "enhanced_cps_poverty_rate": eg["poverty_rate"],
                "raw_cps_child_share": rg["child_share"],
                "enhanced_cps_child_share": eg["child_share"],
            }
        )

    # Filter out groups with no children in either dataset
    merged = [
        g
        for g in merged
        if g["raw_cps_child_share"] > 0 or g["enhanced_cps_child_share"] > 0
    ]

    return {"groups": merged}
