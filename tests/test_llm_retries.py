from unittest.mock import Mock

import pytest
from google.genai.errors import ClientError, ServerError
from httpx import ReadTimeout
from langchain_core.messages import AIMessage
from pydantic import BaseModel

import app.services.llm_service as module
from app.services.llm_service import LLMService


class Plan(BaseModel):
    title: str


def unavailable():
    return ServerError(503, {"error": {"code": 503, "status": "UNAVAILABLE", "message": "High demand"}})


@pytest.fixture
def setup_retry(monkeypatch):
    delays = []
    monkeypatch.setattr(module, "sleep", delays.append)
    monkeypatch.setattr(module.settings, "llm_max_attempts", 4)
    return delays


def test_structured_call_recovers_without_rebuilding_prompt(monkeypatch, setup_retry):
    service = LLMService()
    result = Plan(title="Recovered plan")
    runnable = Mock()
    runnable.invoke.side_effect = [unavailable(), unavailable(), result]
    factory = Mock(return_value=runnable)
    monkeypatch.setattr(service, "get_structured_llm", factory)

    assert service.invoke_structured("Existing report context", Plan) is result
    factory.assert_called_once_with(Plan)
    assert runnable.invoke.call_count == 3
    messages = runnable.invoke.call_args_list[0].args[0]
    assert all(call.args[0] is messages for call in runnable.invoke.call_args_list)
    assert 2 <= setup_retry[0] <= 3
    assert 4 <= setup_retry[1] <= 5


def test_exhausted_retries_are_bounded_and_readable(monkeypatch, setup_retry):
    service = LLMService()
    runnable = Mock()
    runnable.invoke.side_effect = unavailable()
    monkeypatch.setattr(service, "get_structured_llm", lambda _: runnable)

    with pytest.raises(RuntimeError, match="temporarily unavailable after 4 attempts") as error:
        service.invoke_structured("Report context", Plan)
    assert isinstance(error.value.__cause__, ServerError)
    assert "High demand" not in str(error.value)
    assert runnable.invoke.call_count == 4
    assert len(setup_retry) == 3


@pytest.mark.parametrize("error", [unavailable(), ReadTimeout("Timed out")])
def test_plain_text_recovers(monkeypatch, setup_retry, error):
    service = LLMService()
    runnable = Mock()
    runnable.invoke.side_effect = [error, AIMessage(content="Recovered")]
    monkeypatch.setattr(service, "_get_llm", lambda: runnable)
    assert service.invoke("Context") == "Recovered"
    assert runnable.invoke.call_count == 2


@pytest.mark.parametrize("code", [400, 401, 403, 404, 429])
def test_permanent_or_quota_errors_are_not_retried(monkeypatch, setup_retry, code):
    service = LLMService()
    runnable = Mock()
    runnable.invoke.side_effect = ClientError(code, {"error": {"code": code, "message": "Rejected"}})
    monkeypatch.setattr(service, "get_structured_llm", lambda _: runnable)
    with pytest.raises(RuntimeError, match="Rejected"):
        service.invoke_structured("Context", Plan)
    assert runnable.invoke.call_count == 1
    assert setup_retry == []


def test_invalid_structured_output_is_not_retried(monkeypatch, setup_retry):
    service = LLMService()
    runnable = Mock()
    runnable.invoke.return_value = {"title": "Wrong type"}
    monkeypatch.setattr(service, "get_structured_llm", lambda _: runnable)
    with pytest.raises(RuntimeError, match="expected Plan"):
        service.invoke_structured("Context", Plan)
    assert runnable.invoke.call_count == 1
    assert setup_retry == []
