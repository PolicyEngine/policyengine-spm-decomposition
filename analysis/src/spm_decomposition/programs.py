"""Program effects on child SPM poverty.

For each safety-net program, computes how many children it lifts out of SPM
poverty by subtracting the program's benefit from SPM net income and
recalculating the poverty flag.

All values use the enhanced CPS with PE-computed benefits/taxes.
"""

import numpy as np

from .poverty import _map_spm_to_person


def _calc_as_spm(sim, var_name, period):
    """Compute a variable mapped to SPM-unit level.

    Uses sim.calc(map_to="spm_unit") which correctly sums tax-unit or
    person-level variables to SPM-unit level without double-counting.
    """
    return sim.calc(var_name, period=period, map_to="spm_unit").values


def _program_effect(
    sim, benefit_spm, period, spm_net_income_person, spm_threshold_person
):
    """Compute poverty effect of removing a benefit.

    Parameters
    ----------
    sim : Microsimulation
    benefit_spm : np.ndarray
        SPM-unit-level annual benefit amounts.
    period : int
    spm_net_income_person, spm_threshold_person : np.ndarray
        Person-level net income and threshold (pre-computed).

    Returns
    -------
    dict with keys: children_lifted, total_lifted, rate_with, rate_without,
        total_benefit_B
    """
    is_child = sim.calc("is_child", period=period).values == 1
    pw = sim.calc("person_weight", period=period).values
    child_pw = pw[is_child]

    benefit_person = _map_spm_to_person(sim, benefit_spm, period)
    is_poor = (spm_net_income_person < spm_threshold_person).astype(float)

    net_without = spm_net_income_person - benefit_person
    poor_without = (net_without < spm_threshold_person).astype(float)

    rate_with = float(np.average(is_poor[is_child], weights=child_pw))
    rate_without = float(np.average(poor_without[is_child], weights=child_pw))

    children_lifted = float(((poor_without - is_poor) * pw)[is_child].sum())
    total_lifted = float(((poor_without - is_poor) * pw).sum())

    # Weighted total using SPM-unit weights
    spm_w = np.asarray(
        sim.calc("spm_unit_spm_threshold", period=period).weights
    )
    total_benefit = float((benefit_spm * spm_w).sum())

    return {
        "children_lifted": children_lifted,
        "total_lifted": total_lifted,
        "rate_with": rate_with,
        "rate_without": rate_without,
        "total_benefit_B": total_benefit / 1e9,
    }


def compute_program_effects(sim, period=2024) -> list[dict]:
    """Compute poverty effect of each major safety-net program.

    Returns list of dicts, one per program, with keys:
        program, label, children_lifted, total_lifted,
        rate_with, rate_without, total_benefit_B, census_children_lifted_M
    """
    # Pre-compute shared arrays
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period).values
    spm_net_income = sim.calc("spm_unit_net_income", period=period).values
    spm_threshold_person = _map_spm_to_person(sim, spm_threshold, period)
    spm_net_income_person = _map_spm_to_person(sim, spm_net_income, period)

    def effect(benefit_spm):
        return _program_effect(
            sim, benefit_spm, period,
            spm_net_income_person, spm_threshold_person,
        )

    results = []

    # SNAP — SPM-unit level, PE annualizes monthly vars when period=YEAR
    r = effect(_calc_as_spm(sim, "snap", period))
    r.update(program="snap", label="SNAP", census_children_lifted_M=1.4)
    results.append(r)

    # Social Security — person-level, map_to sums to SPM
    r = effect(_calc_as_spm(sim, "social_security", period))
    r.update(program="social_security", label="Social Security",
             census_children_lifted_M=None)
    results.append(r)

    # SSI — person-level
    r = effect(_calc_as_spm(sim, "ssi", period))
    r.update(program="ssi", label="SSI", census_children_lifted_M=0.5)
    results.append(r)

    # Housing subsidies — SPM-unit level (reported/disabled)
    r = effect(_calc_as_spm(sim, "spm_unit_capped_housing_subsidy", period))
    r.update(program="housing", label="Housing subsidies",
             census_children_lifted_M=None)
    results.append(r)

    # School meals — SPM-unit level (PE-computed)
    free_meals = _calc_as_spm(sim, "free_school_meals", period)
    reduced_meals = _calc_as_spm(sim, "reduced_price_school_meals", period)
    r = effect(free_meals + reduced_meals)
    r.update(program="school_meals", label="School meals",
             census_children_lifted_M=None)
    results.append(r)

    # EITC — tax-unit level, map_to sums to SPM correctly
    eitc_spm = _calc_as_spm(sim, "eitc", period)
    r = effect(eitc_spm)
    r.update(program="eitc", label="EITC", census_children_lifted_M=None)
    results.append(r)

    # Refundable CTC — tax-unit level
    try:
        rctc_spm = _calc_as_spm(sim, "refundable_ctc", period)
        r = effect(rctc_spm)
        r.update(program="refundable_ctc", label="Refundable CTC",
                 census_children_lifted_M=None)
        results.append(r)

        # Combined refundable credits
        r = effect(eitc_spm + rctc_spm)
        r.update(program="refundable_credits", label="EITC + refundable CTC",
                 census_children_lifted_M=3.7)
        results.append(r)
    except Exception:
        pass

    return results
