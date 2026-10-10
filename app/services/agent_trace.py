"""Build safe, compact state handoffs for the live agent trace UI."""

from typing import Any, Mapping

from app.graph.state import ProjectState

AGENT_INPUT_FIELDS: dict[str, tuple[str, ...]] = {
    "supervisor": ("user_idea",),
    "research": ("requirements",),
    "rag": ("requirements", "research_results"),
    "architect": ("requirements", "research_results", "retrieved_context"),
    "critic": ("requirements", "architecture", "dataset_strategy", "model_strategy"),
    "report": (
        "requirements",
        "research_results",
        "retrieved_context",
        "architecture",
        "dataset_strategy",
        "model_strategy",
        "critic_feedback",
    ),
}

AGENT_OUTPUT_FIELDS: dict[str, tuple[str, ...]] = {
    "supervisor": ("requirements",),
    "research": ("research_results", "sources"),
    "rag": ("retrieved_context",),
    "architect": ("architecture", "dataset_strategy", "model_strategy"),
    "critic": ("critic_feedback", "revision_count", "revision_target"),
    "report": ("final_report",),
}

MAX_STRING_LENGTH = 2400
MAX_LIST_ITEMS = 12
MAX_DICT_ITEMS = 30
MAX_DEPTH = 5


def _compact(value: Any, depth: int = 0) -> Any:
    if depth >= MAX_DEPTH:
        return "[nested content omitted]"
    if isinstance(value, str):
        if len(value) <= MAX_STRING_LENGTH:
            return value
        return value[:MAX_STRING_LENGTH].rstrip() + "\n...[truncated]"
    if isinstance(value, Mapping):
        items = list(value.items())
        compacted = {
            str(key): _compact(item, depth + 1)
            for key, item in items[:MAX_DICT_ITEMS]
        }
        if len(items) > MAX_DICT_ITEMS:
            compacted["_omitted_fields"] = len(items) - MAX_DICT_ITEMS
        return compacted
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        compacted = [_compact(item, depth + 1) for item in items[:MAX_LIST_ITEMS]]
        if len(items) > MAX_LIST_ITEMS:
            compacted.append(f"...[{len(items) - MAX_LIST_ITEMS} more items]")
        return compacted
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _select(source: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {
        field: _compact(source.get(field))
        for field in fields
        if field in source and source.get(field) not in ({}, [], "", None)
    }


def build_agent_trace_step(
    node: str,
    state_before: ProjectState,
    update: Mapping[str, Any],
    sequence: int,
) -> tuple[dict[str, Any], ProjectState]:
    """Describe one completed node and the exact state handed to its successor."""
    state_after = ProjectState(**state_before)
    state_after.update(update)
    next_agent = update.get("current_agent")
    next_fields = AGENT_INPUT_FIELDS.get(str(next_agent), ())

    step = {
        "sequence": sequence,
        "agent": node,
        "input": _select(state_before, AGENT_INPUT_FIELDS.get(node, ())),
        "output": _select(update, AGENT_OUTPUT_FIELDS.get(node, ())),
        "handoff_to": next_agent if next_agent in AGENT_INPUT_FIELDS else None,
        "next_input": _select(state_after, next_fields),
        "revision_count": update.get(
            "revision_count",
            state_after.get("revision_count", 0),
        ),
    }
    return step, state_after
