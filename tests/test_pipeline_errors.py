from unittest.mock import Mock

import pytest

from app.graph import workflow


@pytest.mark.parametrize("streaming", [False, True])
def test_failed_supervisor_stops_pipeline(monkeypatch, streaming):
    research = Mock()
    monkeypatch.setattr(workflow, "run_supervisor", lambda state: {
        "requirements": {}, "error": "Model unavailable (404)"
    })
    monkeypatch.setattr(workflow, "run_research_agent", research)
    monkeypatch.setattr(workflow, "graph", workflow.build_graph())

    with pytest.raises(RuntimeError, match="supervisor: Model unavailable"):
        if streaming:
            list(workflow.stream_pipeline("Build a student chatbot"))
        else:
            workflow.run_pipeline("Build a student chatbot")
    research.assert_not_called()


def test_empty_report_is_not_success():
    node = workflow.checked_node("report", lambda state: {"final_report": {}})
    with pytest.raises(RuntimeError, match="No report was generated"):
        node({})
