from unittest.mock import Mock

import httpx
import pytest

import app.tools.dataset_search as tool
from app.agents import report_agent, research_agent
from app.models.dataset_models import DatasetRecommendation, DatasetSelection
from app.models.report_models import FinalProjectPlan
from app.models.research_models import ResearchResult
from app.tools.web_search import WebSearchResponse, WebSearchResult


def candidate():
    return tool.DatasetInfo(
        name="stanfordnlp/imdb", source="https://huggingface.co/datasets/stanfordnlp/imdb",
        description="Movie reviews for sentiment classification.", provider="Hugging Face",
        discovery_source="Hugging Face API", data_type="text", size="10K<n<100K", license="Unknown in fixture",
    )


def discovery():
    return tool.DatasetSearchResponse(query="sentiment", project_type="nlp", datasets=[candidate()])


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "http://huggingface.co/datasets/a/b", "https://huggingface.co.evil.test/datasets/a/b",
    "https://huggingface.co@evil.test/datasets/a/b", "https://kaggle.com/datasets", "https://archive.ics.uci.edu/",
    "https://localhost/datasets/a/b", "https://huggingface.co:8000/datasets/a/b",
    "https://huggingface.co/datasets/../secret", "https://kaggle.com/code/user/notebook",
])
def test_rejects_non_dataset_or_unsafe_pages(url):
    assert tool.dataset_page(url) is None


def test_selection_resolves_only_real_candidates_and_deduplicates():
    results = discovery().resolve([
        DatasetSelection(candidate_id="made-up", relevance="Invented"),
        DatasetSelection(candidate_id="dataset-1", relevance="Useful sentiment baseline, not domain-specific."),
        DatasetSelection(candidate_id="dataset-1", relevance="Duplicate"),
    ])
    assert len(results) == 1
    assert results[0].url == candidate().source
    assert results[0].access is None
    assert results[0].description == candidate().description


def test_catalog_metadata_comes_from_api(monkeypatch):
    def respond(request):
        assert request.url.params["full"] == "true"
        return httpx.Response(200, json=[{
            "id": "owner/dataset", "description": "Source description", "gated": "manual",
            "tags": ["license:apache-2.0", "size_categories:1K<n<10K", "modality:image"],
        }, {"id": "owner/private", "private": True}, {"id": "../invalid"}])
    client_type = httpx.Client
    monkeypatch.setattr(tool.httpx, "Client", lambda **kwargs: client_type(transport=httpx.MockTransport(respond), **kwargs))
    result = tool._search_huggingface("defect")
    assert len(result) == 1
    assert result[0].license == "apache-2.0"
    assert result[0].size == "1K<n<10K"
    assert result[0].data_type == "image"
    assert "approval" in result[0].access


def test_search_keeps_actual_kaggle_uci_pages_and_unknown_metadata(monkeypatch):
    monkeypatch.setattr(tool, "_search_huggingface", lambda *args, **kwargs: [candidate()])
    search = Mock(return_value=WebSearchResponse(query="churn", results=[
        WebSearchResult("Churn", "https://www.kaggle.com/datasets/owner/churn?tracking=1", "Customer churn data"),
        WebSearchResult("Bank", "https://archive.ics.uci.edu/dataset/222/bank+marketing", "Marketing data"),
        WebSearchResult("Hub", "https://kaggle.com/datasets", "Not a dataset"),
        WebSearchResult("Fake", "https://kaggle.com.bad.test/datasets/a/b", "Not trusted"),
    ]))
    monkeypatch.setattr(tool, "web_search", search)
    result = tool.dataset_search("general", project_title="Customer churn prediction", max_results=3)
    assert len(result.datasets) == 3
    assert search.call_args.kwargs["include_domains"] == tool.DATASET_DOMAINS
    assert result.datasets[1].source == "https://www.kaggle.com/datasets/owner/churn"
    assert result.datasets[1].license is None
    assert result.datasets[2].provider == "UCI"


def test_no_results_does_not_fill_with_curated_guesses(monkeypatch):
    monkeypatch.setattr(tool, "_search_huggingface", lambda *args, **kwargs: [])
    monkeypatch.setattr(tool, "web_search", lambda *args, **kwargs: WebSearchResponse(query="x", success=False))
    result = tool.dataset_search("rag", domain="private course material")
    assert result.datasets == []
    assert result.error
    assert "empty" in result.to_formatted_string()


def test_research_preserves_selected_tool_facts(monkeypatch):
    response = discovery()
    monkeypatch.setattr(research_agent.search_service, "run_research_search", lambda **kwargs: (
        "Web results", response.to_formatted_string(), [candidate().source], response,
    ))
    monkeypatch.setattr(research_agent.llm_service, "invoke_structured", lambda **kwargs: ResearchResult(
        summary="Research", key_findings=["Text classification"],
        dataset_hints=["Invented dataset"],
        dataset_selections=[DatasetSelection(candidate_id="dataset-1", relevance="Movie-review sentiment baseline.")],
    ))
    state = research_agent.run_research_agent({"requirements": {"project_title": "Sentiment", "project_type": "nlp"}})
    result = state["research_results"]
    assert result["dataset_recommendations"][0]["url"] == candidate().source
    assert "Invented dataset" not in str(result["dataset_hints"])


def test_final_report_cannot_replace_researched_links(monkeypatch):
    recommendations = discovery().resolve([DatasetSelection(candidate_id="dataset-1", relevance="Sentiment baseline.")])
    plan = FinalProjectPlan(
        project_title="Sentiment", executive_summary="Test", objectives=["Classify"], technical_architecture="API",
        dataset_plan="Use movie reviews.", model_plan="Classifier", implementation_roadmap=["Train"],
        success_metrics=["F1"], estimated_timeline_weeks=2,
        dataset_recommendations=[DatasetRecommendation(name="Invented", url="https://bad.test/dataset",
            description="Fake", relevance="Fake", provider="Fake", discovery_source="Fake")],
    )
    monkeypatch.setattr(report_agent.llm_service, "invoke_structured", lambda **kwargs: plan)
    result = report_agent.run_report_agent({
        "requirements": {"project_title": "Sentiment"}, "architecture": {"system_overview": "API"},
        "research_results": {"dataset_recommendations": [item.model_dump() for item in recommendations], "dataset_discovery_note": "From live search"},
    })
    report = result["final_report"]
    assert report["dataset_recommendations"][0]["url"] == candidate().source
    assert "bad.test" not in str(report["dataset_recommendations"])
    assert report["dataset_discovery_note"] == "From live search"
    assert candidate().source in report["sources"]
