"""Tests for the optional LangSmith configuration."""

import os

from app.services import tracing


def test_langsmith_stays_disabled_without_an_api_key(monkeypatch):
    monkeypatch.setattr(tracing.settings, "langsmith_tracing", True)
    monkeypatch.setattr(tracing.settings, "langsmith_api_key", "")
    monkeypatch.setenv("LANGSMITH_API_KEY", "stale-key")
    monkeypatch.setenv("LANGSMITH_PROJECT", "stale-project")

    assert tracing.configure_langsmith() is False
    assert os.environ["LANGSMITH_TRACING"] == "false"
    assert "LANGSMITH_API_KEY" not in os.environ
    assert "LANGSMITH_PROJECT" not in os.environ


def test_langsmith_configuration_and_pipeline_metadata(monkeypatch):
    monkeypatch.setattr(tracing.settings, "langsmith_tracing", True)
    monkeypatch.setattr(tracing.settings, "langsmith_api_key", "lsv2_test_key")
    monkeypatch.setattr(tracing.settings, "langsmith_project", "test-project")
    monkeypatch.setattr(
        tracing.settings,
        "langsmith_endpoint",
        "https://api.smith.langchain.com",
    )

    assert tracing.configure_langsmith() is True
    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "lsv2_test_key"
    assert os.environ["LANGSMITH_PROJECT"] == "test-project"

    config = tracing.pipeline_trace_config()
    assert config["run_name"] == "Planorai Pipeline"
    assert config["metadata"]["llm_model"] == tracing.settings.llm_model
    assert "lsv2_test_key" not in repr(config)
