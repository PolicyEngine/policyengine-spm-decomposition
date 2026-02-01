"""State-level poverty rate computation.

This module loads real PE microsimulations for each state and is therefore
expensive to run.  Mark any tests that call these functions as
``@pytest.mark.slow``.
"""

from .config import STATES, STATE_DATASET_TEMPLATE, YEAR
from .poverty import compute_child_poverty_rate


def compute_state_results(period=YEAR) -> list[dict]:
    """Compute reported and PE-computed child poverty for every state.

    Parameters
    ----------
    period : int
        Tax year.

    Returns
    -------
    list[dict]
        One dict per state with keys: ``state``, ``reported_child_poverty``,
        ``computed_child_poverty``, ``total_children``.
    """
    # Import here to avoid slow import at module level when not needed
    from policyengine_us import Microsimulation

    results = []
    for state in STATES:
        dataset_path = STATE_DATASET_TEMPLATE.format(state=state)
        sim = Microsimulation(dataset=dataset_path)
        poverty = compute_child_poverty_rate(sim, period=period)

        # Total weighted children
        is_child = sim.calc("is_child", period=period)
        person_weight = sim.calc("person_weight", period=period)
        child_mask = is_child.values == 1
        total_children = float(person_weight.values[child_mask].sum())

        results.append(
            {
                "state": state,
                "reported_child_poverty": poverty["reported"],
                "computed_child_poverty": poverty["computed"],
                "total_children": total_children,
            }
        )

    return results
