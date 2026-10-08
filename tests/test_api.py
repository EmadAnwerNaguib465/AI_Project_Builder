import json

from fastapi.testclient import TestClient

import api as api_module


def test_build_streams_steps_and_report(monkeypatch):
    monkeypatch.setattr(api_module.settings, "google_api_key", "test-key")

    def pipeline(_idea):
        yield "supervisor", {"requirements": {"project_title": "Demo"}, "current_agent": "research"}
        yield "report", {"final_report": {"project_title": "Demo"}, "current_agent": "done"}

    monkeypatch.setattr(api_module, "stream_pipeline", pipeline)
    response = TestClient(api_module.api).post("/build", json={"idea": "Build a student chatbot for course documents"})
    messages = [json.loads(line) for line in response.text.splitlines()]
    assert response.status_code == 200
    assert [message["type"] for message in messages] == ["started", "step", "step", "complete"]
    assert messages[-1]["report"]["project_title"] == "Demo"


def test_build_reports_agent_error(monkeypatch):
    monkeypatch.setattr(api_module.settings, "google_api_key", "test-key")

    def pipeline(_idea):
        raise RuntimeError("supervisor: Model unavailable")
        yield

    monkeypatch.setattr(api_module, "stream_pipeline", pipeline)
    response = TestClient(api_module.api).post("/build", json={"idea": "Build a student chatbot for course documents"})
    assert json.loads(response.text.splitlines()[-1]) == {
        "type": "error", "message": "supervisor: Model unavailable"
    }


def test_build_rejects_short_idea(monkeypatch):
    monkeypatch.setattr(api_module.settings, "google_api_key", "test-key")
    response = TestClient(api_module.api).post("/build", json={"idea": "short"})
    assert response.status_code == 422
