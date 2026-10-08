from unittest.mock import Mock

from langchain_core.messages import AIMessage

from app.services.llm_service import LLMService


def test_invoke_extracts_text_from_content_blocks(monkeypatch):
    service = LLMService()
    llm = Mock()
    llm.invoke.return_value = AIMessage(content=[{"type": "text", "text": "Grounded context"}])
    monkeypatch.setattr(service, "_get_llm", lambda: llm)

    assert service.invoke("Summarize this") == "Grounded context"
