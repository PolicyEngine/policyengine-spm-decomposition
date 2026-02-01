"""Demographic breakdowns of SPM child poverty."""

import numpy as np

from .poverty import _map_spm_to_person


def compute_demographic_breakdowns(sim, period=2024) -> dict:
    """Compute child poverty rates by age group and race/ethnicity.

    Returns dict with keys 'by_age' and 'by_race', each a list of dicts.
    """
    is_child = sim.calc("is_child", period=period).values == 1
    pw = sim.calc("person_weight", period=period).values
    age = sim.calc("age", period=period).values

    # Compute poverty from SPM net income
    spm_threshold = sim.calc("spm_unit_spm_threshold", period=period).values
    spm_net_income = sim.calc("spm_unit_net_income", period=period).values
    threshold_person = _map_spm_to_person(sim, spm_threshold, period)
    net_income_person = _map_spm_to_person(sim, spm_net_income, period)
    is_poor = (net_income_person < threshold_person).astype(float)

    # By age group
    by_age = []
    for age_min, age_max, label, census_rate in [
        (0, 5, "Under 6", 0.151),
        (6, 11, "6-11", 0.126),
        (12, 17, "12-17", 0.125),
    ]:
        mask = is_child & (age >= age_min) & (age <= age_max)
        if np.any(mask):
            rate = float(np.average(is_poor[mask], weights=pw[mask]))
            count = float(pw[mask].sum())
        else:
            rate = 0.0
            count = 0.0
        by_age.append({
            "group": label,
            "pe_rate": round(rate, 4),
            "census_rate": census_rate,
            "total_children": round(count),
        })

    # By race/ethnicity
    by_race = []
    try:
        cps_race = sim.calc("cps_race", period=period).values
        for code, label, census_rate in [
            (1, "White", 0.11),
            (2, "Black", 0.21),
            (3, "American Indian", None),
            (4, "Asian", 0.11),
        ]:
            mask = is_child & (cps_race == code)
            if np.any(mask):
                rate = float(np.average(is_poor[mask], weights=pw[mask]))
                count = float(pw[mask].sum())
            else:
                rate = 0.0
                count = 0.0
            by_race.append({
                "group": label,
                "pe_rate": round(rate, 4),
                "census_rate": census_rate,
                "total_children": round(count),
            })
    except Exception:
        pass

    try:
        is_hispanic = sim.calc("is_hispanic", period=period).values
        for val, label, census_rate in [
            (1, "Hispanic (any race)", 0.20),
            (0, "Non-Hispanic", None),
        ]:
            mask = is_child & (is_hispanic == val)
            if np.any(mask):
                rate = float(np.average(is_poor[mask], weights=pw[mask]))
                count = float(pw[mask].sum())
            else:
                rate = 0.0
                count = 0.0
            by_race.append({
                "group": label,
                "pe_rate": round(rate, 4),
                "census_rate": census_rate,
                "total_children": round(count),
            })
    except Exception:
        pass

    return {"by_age": by_age, "by_race": by_race}
