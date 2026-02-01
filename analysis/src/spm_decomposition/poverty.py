"""Child poverty rate computation using PolicyEngine microsimulation results."""

import numpy as np


def _map_spm_to_person(sim, spm_values, period):
    """Map SPM-unit-level values to person level.

    Parameters
    ----------
    sim : Microsimulation
        PolicyEngine sim with spm_unit_id and person_spm_unit_id.
    spm_values : np.ndarray
        Values at the SPM-unit level.
    period : int
        Tax year.

    Returns
    -------
    np.ndarray
        Values broadcast to person level.
    """
    spm_unit_id = sim.calc("spm_unit_id", period=period).values
    person_spm_unit_id = sim.calc("person_spm_unit_id", period=period).values
    spm_id_to_idx = {int(sid): i for i, sid in enumerate(spm_unit_id)}
    return np.array([spm_values[spm_id_to_idx[int(pid)]] for pid in person_spm_unit_id])


def compute_child_poverty_rate(sim, period=2024) -> dict:
    """Compute PE-computed and CPS-reported child poverty rates.

    Parameters
    ----------
    sim : Microsimulation (or mock)
        A PolicyEngine Microsimulation instance supporting ``sim.calc(var, period)``.
    period : int
        Tax year to compute for.

    Returns
    -------
    dict
        ``{"computed": float, "reported": float}`` — weighted child poverty rates.
        "reported" uses spm_unit_net_income_reported vs spm_unit_spm_threshold,
        mapped from SPM-unit level to person level.
    """
    is_child = sim.calc("is_child", period=period)
    child_mask = is_child.values == 1

    # If no children in the data, return 0 for both
    if not np.any(child_mask):
        return {"computed": 0.0, "reported": 0.0}

    person_weight = sim.calc("person_weight", period=period).values

    # PE-computed poverty (person_in_poverty already reflects PE tax/benefit modelling)
    person_in_poverty = sim.calc("person_in_poverty", period=period)
    computed_rate = float(
        np.average(person_in_poverty.values[child_mask], weights=person_weight[child_mask])
    )

    # CPS-reported poverty: compare reported SPM resources to SPM threshold
    # These are SPM-unit level variables — map to person level
    net_income_reported = sim.calc("spm_unit_net_income_reported", period=period)
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period)
    reported_poor_spm = (net_income_reported.values < spm_threshold.values).astype(float)

    person_reported_poor = _map_spm_to_person(sim, reported_poor_spm, period)
    reported_rate = float(
        np.average(person_reported_poor[child_mask], weights=person_weight[child_mask])
    )

    return {"computed": float(computed_rate), "reported": float(reported_rate)}
