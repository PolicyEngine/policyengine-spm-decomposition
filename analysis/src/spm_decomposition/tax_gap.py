"""Federal tax gap by income decile: PE-computed vs CPS-reported federal tax."""

import numpy as np


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


def _assign_decile(values, weights):
    """Assign each observation to an income decile (0-9)."""
    breakpoints = _weighted_quantiles(
        values, weights, [i / 10 for i in range(1, 10)]
    )
    decile = np.zeros(len(values), dtype=int)
    for i, bp in enumerate(breakpoints):
        decile[values > bp] = i + 1
    return decile


def compute_tax_gap(sim, period=2024) -> list[dict]:
    """Compute mean PE vs reported federal tax by income decile.

    Uses SPM-unit level variables:
    - spm_unit_total_income_reported for income decile grouping
    - spm_unit_federal_tax (PE-computed)
    - spm_unit_federal_tax_reported (CPS-reported)

    Parameters
    ----------
    sim : Microsimulation
        Microsimulation instance (or mock).
    period : int
        Tax year.

    Returns
    -------
    list[dict]
        10 dicts, one per decile, each with keys:
        ``decile``, ``mean_income``, ``pe_federal_tax``,
        ``reported_federal_tax``, ``gap``.
    """
    income = sim.calc("spm_unit_total_income_reported", period=period)
    tax_pe = sim.calc("spm_unit_federal_tax", period=period)
    tax_reported = sim.calc("spm_unit_federal_tax_reported", period=period)

    values = np.asarray(income.values, dtype=float)
    weights = np.asarray(income.weights, dtype=float)
    deciles = _assign_decile(values, weights)

    results = []
    for d in range(10):
        mask = deciles == d
        if np.any(mask):
            w = weights[mask]
            mean_inc = float(np.average(values[mask], weights=w))
            mean_pe_tax = float(np.average(tax_pe.values[mask], weights=w))
            mean_reported_tax = float(
                np.average(tax_reported.values[mask], weights=w)
            )
        else:
            mean_inc = 0.0
            mean_pe_tax = 0.0
            mean_reported_tax = 0.0

        results.append(
            {
                "decile": d + 1,
                "mean_income": mean_inc,
                "pe_federal_tax": mean_pe_tax,
                "reported_federal_tax": mean_reported_tax,
                "gap": mean_pe_tax - mean_reported_tax,
            }
        )

    return results
