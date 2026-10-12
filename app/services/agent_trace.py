"""Build compact, JSON-serializable snapshots for the web execution trace."""

from copy import deepcopy
from typing import Any


def build_agent_trace_step(
    node: str,
    trace_state: dict[str, Any],
    update: dict[str, Any],
    sequence: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a trace entry and the accumulated state after this graph node."""
    before = deepcopy(trace_state)
    after = {**trace_state, **update}
    step = {
        "sequence": sequence,
        "node": node,
        "input": before,
        "output": deepcopy(update),
        "state_after": deepcopy(after),
    }
    return step, after
