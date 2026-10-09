"""Discover dataset pages from live catalog/search results; no invented fallbacks."""

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

import httpx

from app.models.dataset_models import DatasetRecommendation, DatasetSelection
from app.tools.web_search import web_search
from app.utils.logger import get_logger

logger = get_logger(__name__)
HF_DATASETS_API = "https://huggingface.co/api/datasets"
HF_SEARCH_TIMEOUT = 8.0
DATASET_DOMAINS = ["huggingface.co", "kaggle.com", "archive.ics.uci.edu"]


def dataset_page(url: str) -> tuple[str, str] | None:
    """Only allow actual catalog detail pages, not search pages or lookalike hosts."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
            return None
        host = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/")
        if host == "huggingface.co" and re.fullmatch(r"/datasets/[\w.-]+/[\w.-]+", path):
            provider = "Hugging Face"
        elif host in {"kaggle.com", "www.kaggle.com"} and re.fullmatch(r"/datasets/[\w-]+/[\w-]+", path):
            provider, host = "Kaggle", "www.kaggle.com"
        elif host == "archive.ics.uci.edu" and re.fullmatch(r"/dataset/\d+(?:/[^/]+)?", path):
            provider = "UCI"
        else:
            return None
        if any(part in {".", ".."} for part in path.split("/")):
            return None
        return urlunsplit(("https", host, path, "", "")), provider
    except (TypeError, ValueError):
        return None


@dataclass
class DatasetInfo:
    name: str
    source: str
    description: str
    downloads: int | None = None
    tags: list[str] = field(default_factory=list)
    provider: str = ""
    discovery_source: str = ""
    data_type: str | None = None
    size: str | None = None
    license: str | None = None
    access: str | None = None


@dataclass
class DatasetSearchResponse:
    query: str
    project_type: str
    datasets: list[DatasetInfo] = field(default_factory=list)
    source: str = "live search"
    error: str | None = None

    def to_formatted_string(self) -> str:
        if not self.datasets:
            return "No source-backed dataset candidates were found. Return an empty dataset_selections list."
        return json.dumps([
            {"candidate_id": f"dataset-{index}", "name": dataset.name,
             "url": dataset.source, "description": dataset.description,
             "data_type": dataset.data_type, "size": dataset.size,
             "license": dataset.license, "access": dataset.access}
            for index, dataset in enumerate(self.datasets, 1)
        ], ensure_ascii=False)

    def resolve(self, selections: list[DatasetSelection]) -> list[DatasetRecommendation]:
        candidates = {f"dataset-{index}": dataset for index, dataset in enumerate(self.datasets, 1)}
        recommendations = []
        seen = set()
        for selection in selections[:5]:
            dataset = candidates.get(selection.candidate_id)
            if not dataset or not selection.relevance.strip():
                continue
            page = dataset_page(dataset.source)
            if not page or page[0] in seen:
                continue
            seen.add(page[0])
            recommendations.append(DatasetRecommendation(
                name=dataset.name, url=page[0], provider=page[1],
                description=dataset.description, relevance=selection.relevance,
                discovery_source=dataset.discovery_source,
                data_type=dataset.data_type, size=dataset.size,
                license=dataset.license, access=dataset.access,
            ))
        return recommendations


def _tag_value(tags: list[str], prefix: str) -> str | None:
    values = [tag[len(prefix):] for tag in tags if tag.startswith(prefix)]
    return ", ".join(values) if values else None


def _search_huggingface(query: str, max_results: int = 5) -> list[DatasetInfo]:
    try:
        with httpx.Client(timeout=HF_SEARCH_TIMEOUT) as client:
            response = client.get(HF_DATASETS_API, params={
                "search": query, "limit": max_results, "sort": "downloads", "direction": -1, "full": "true",
            })
            response.raise_for_status()
        datasets = []
        for item in response.json():
            identifier = item.get("id", "")
            page = dataset_page(f"https://huggingface.co/datasets/{identifier}")
            if not page or item.get("private"):
                continue
            tags = [tag for tag in item.get("tags", []) if isinstance(tag, str)]
            gated = item.get("gated")
            access = "Account and access approval required" if gated in {"auto", "manual"} else (
                "Public repository; check the dataset terms" if gated is False else None
            )
            datasets.append(DatasetInfo(
                name=identifier, source=page[0], provider=page[1],
                description=(item.get("description") or "No description returned by the catalog.")[:1200],
                downloads=item.get("downloads"), tags=tags,
                discovery_source="Hugging Face API",
                data_type=_tag_value(tags, "modality:"),
                size=_tag_value(tags, "size_categories:"),
                license=_tag_value(tags, "license:"), access=access,
            ))
        return datasets
    except Exception as exc:
        logger.warning("Dataset catalog search unavailable: %s", type(exc).__name__)
        return []


def dataset_search(project_type: str, domain: str = "", max_results: int = 5,
                   project_title: str = "", objectives: list[str] | None = None) -> DatasetSearchResponse:
    limit = min(max(max_results, 1), 10)
    context = " ".join([project_title, domain, " ".join((objectives or [])[:1])]).strip()
    query = (context or project_type.replace("_", " "))[:320] + " dataset"
    # Search the task, not a generic AI category. These are query terms, not dataset suggestions.
    terms = [term for term in ["sentiment", "churn", "defect", "fraud", "recommendation", "forecast", "question answering"]
             if term in context.lower()]
    hub_query = terms[0] if terms else (domain or project_type.replace("_", " "))[:100]
    catalog = _search_huggingface(hub_query, max_results=limit)
    web = web_search(query, max_results=limit, include_domains=DATASET_DOMAINS)
    candidates = list(catalog)
    for item in web.results:
        page = dataset_page(item.url)
        if page:
            candidates.append(DatasetInfo(
                name=item.title, source=page[0], description=item.content[:1200],
                provider=page[1], discovery_source="Web search",
            ))
    unique = {}
    for candidate in candidates:
        unique.setdefault(candidate.source, candidate)
    # Keep both search providers available for the research agent's relevance selection.
    return DatasetSearchResponse(query=query, project_type=project_type, datasets=list(unique.values())[:limit * 2],
                                 error=None if unique else "No live dataset candidates available.")
