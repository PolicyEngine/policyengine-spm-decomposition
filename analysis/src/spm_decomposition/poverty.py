"""Child poverty rate computation using PolicyEngine microsimulation results."""

import numpy as np


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
    """
    is_child = sim.calc("is_child", period=period)
    child_mask = is_child.values == 1

    # If no children in the data, return 0 for both
    if not np.any(child_mask):
        return {"computed": 0.0, "reported": 0.0}

    # PE-computed poverty (person_in_poverty already reflects PE tax/benefit modelling)
    person_in_poverty = sim.calc("person_in_poverty", period=period)
    computed_rate = person_in_poverty[child_mask].mean()

    # CPS-reported poverty: compare reported SPM resources to SPM threshold
    net_income_reported = sim.calc("spm_unit_net_income_reported", period=period)
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period)
    reported_poor = net_income_reported < spm_threshold
    reported_rate = reported_poor[child_mask].mean()

    return {"computed": float(computed_rate), "reported": float(reported_rate)}
