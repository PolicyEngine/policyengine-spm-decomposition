"""Poverty rate computation using PolicyEngine microsimulation results."""

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

    Returns
    -------
    dict
        ``{"computed": float, "reported": float}`` -- weighted child poverty rates.
    """
    is_child = sim.calc("is_child", period=period)
    child_mask = is_child.values == 1

    if not np.any(child_mask):
        return {"computed": 0.0, "reported": 0.0}

    person_weight = sim.calc("person_weight", period=period).values

    person_in_poverty = sim.calc("person_in_poverty", period=period)
    computed_rate = float(
        np.average(person_in_poverty.values[child_mask], weights=person_weight[child_mask])
    )

    net_income_reported = sim.calc("spm_unit_net_income_reported", period=period)
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period)
    reported_poor_spm = (net_income_reported.values < spm_threshold.values).astype(float)

    person_reported_poor = _map_spm_to_person(sim, reported_poor_spm, period)
    reported_rate = float(
        np.average(person_reported_poor[child_mask], weights=person_weight[child_mask])
    )

    return {"computed": float(computed_rate), "reported": float(reported_rate)}


def compute_all_person_poverty_rate(sim, period=2024) -> dict:
    """Compute PE-computed and CPS-reported all-person poverty rates.

    Returns
    -------
    dict
        ``{"computed": float, "reported": float}`` -- weighted all-person poverty rates.
    """
    person_weight = sim.calc("person_weight", period=period).values

    person_in_poverty = sim.calc("person_in_poverty", period=period)
    computed_rate = float(
        np.average(person_in_poverty.values, weights=person_weight)
    )

    net_income_reported = sim.calc("spm_unit_net_income_reported", period=period)
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period)
    reported_poor_spm = (net_income_reported.values < spm_threshold.values).astype(float)

    person_reported_poor = _map_spm_to_person(sim, reported_poor_spm, period)
    reported_rate = float(
        np.average(person_reported_poor, weights=person_weight)
    )

    return {"computed": float(computed_rate), "reported": float(reported_rate)}
