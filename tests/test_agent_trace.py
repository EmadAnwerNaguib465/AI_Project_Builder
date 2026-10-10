from app.graph.state import initial_state
from app.services.agent_trace import build_agent_trace_step


def test_trace_step_shows_output_and_next_agent_input():
    before = initial_state("Build a course assistant from university PDFs")
    update = {
        "requirements": {
            "project_title": "Course Assistant",
            "project_type": "rag",
        },
        "current_agent": "research",
    }

    step, after = build_agent_trace_step("supervisor", before, update, 1)

    assert step["input"] == {"user_idea": before["user_idea"]}
    assert step["output"] == {"requirements": update["requirements"]}
    assert step["handoff_to"] == "research"
    assert step["next_input"] == {"requirements": update["requirements"]}
    assert after["requirements"] == update["requirements"]


def test_trace_step_limits_large_values():
    before = initial_state("Build a research assistant")
    before["requirements"] = {"project_title": "Research Assistant"}
    update = {
        "retrieved_context": "x" * 3000,
        "current_agent": "architect",
    }

    step, _ = build_agent_trace_step("rag", before, update, 3)

    assert step["output"]["retrieved_context"].endswith("...[truncated]")
    assert len(step["output"]["retrieved_context"]) < 2500
