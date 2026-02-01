"""Weight rebalancing analysis: how Enhanced CPS re-weighting shifts child poverty."""

import numpy as np

from .config import INCOME_QUINTILE_LABELS, FAMILY_STRUCTURE_LABELS


def _weighted_quantiles(values, weights, quantiles):
    """Compute weighted quantiles.

    Parameters
    ----------
    values : np.ndarray
    weights : np.ndarray
    quantiles : list[float]
        Values in [0, 1].

    Returns
    -------
    np.ndarray
        Quantile thresholds.
    """
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
    """Assign each observation to an income quintile (0-4).

    Uses the person-level weighted distribution of ``values`` to define
    quintile breakpoints, then assigns each person accordingly.
    """
    breakpoints = _weighted_quantiles(values, weights, [0.2, 0.4, 0.6, 0.8])
    quintile = np.zeros(len(values), dtype=int)
    for i, bp in enumerate(breakpoints):
        quintile[values > bp] = i + 1
    return quintile


def _compute_group_stats(sim, quintiles, family_is_joint, period):
    """Compute per-group child poverty rate and child share for one simulation."""
    is_child = sim.calc("is_child", period=period).values
    person_in_poverty = sim.calc("person_in_poverty", period=period).values
    weights = sim.calc("is_child", period=period)._weights
    child_mask = is_child == 1

    total_children_weighted = float(np.sum(weights[child_mask]))
    groups = []

    for q_idx, q_label in enumerate(INCOME_QUINTILE_LABELS):
        for fs_idx, fs_label in enumerate(FAMILY_STRUCTURE_LABELS):
            is_joint_val = float(fs_idx)  # 0 = single parent, 1 = married
            mask = (
                child_mask
                & (quintiles == q_idx)
                & (family_is_joint == is_joint_val)
            )
            weighted_children = float(np.sum(weights[mask]))
            if weighted_children > 0:
                poverty_rate = float(
                    np.average(person_in_poverty[mask], weights=weights[mask])
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
    # Quintiles are defined on the RAW CPS income distribution
    raw_income = raw_sim.calc("spm_unit_net_income_reported", period=period)
    raw_weights = raw_income._weights
    quintiles_raw = _assign_quintile(raw_income.values, raw_weights)

    # For enhanced sim, compute quintiles on its own distribution
    enh_income = enhanced_sim.calc("spm_unit_net_income_reported", period=period)
    enh_weights = enh_income._weights
    quintiles_enh = _assign_quintile(enh_income.values, enh_weights)

    # Family structure: use tax_unit_is_joint as proxy
    raw_joint = raw_sim.calc("tax_unit_is_joint", period=period).values
    enh_joint = enhanced_sim.calc("tax_unit_is_joint", period=period).values

    raw_groups = _compute_group_stats(raw_sim, quintiles_raw, raw_joint, period)
    enh_groups = _compute_group_stats(enhanced_sim, quintiles_enh, enh_joint, period)

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
