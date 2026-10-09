"""
app/services/search_service.py

Search orchestration service used by the Research Agent.

Coordinates calls to web_search and dataset_search tools,
then returns formatted strings ready for LLM prompt injection.

Usage:
    from app.services.search_service import SearchService
    svc = SearchService()
    web_str, dataset_str, sources, datasets = svc.run_research_search(requirements)
"""

from app.models.state_models import Requirements
from app.tools.web_search import web_search, WebSearchResponse
from app.tools.dataset_search import dataset_search, DatasetSearchResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    """
    Orchestrates the web_search and dataset_search tools for the Research Agent.

    Builds appropriate queries from the project requirements, executes both
    searches, and returns formatted strings for LLM prompt injection.
    """

    def run_research_search(
        self,
        requirements: dict,
        max_web_results: int = 5,
        max_dataset_results: int = 5,
    ) -> tuple[str, str, list[str], DatasetSearchResponse]:
        """
        Runs web search and dataset search for a given set of requirements.

        Args:
            requirements: The Requirements model as a dict (from state).
            max_web_results: Maximum web results to fetch.
            max_dataset_results: Maximum dataset results to fetch.

        Returns:
            Tuple of:
                - web_results_str (str): Formatted web search results for prompt injection
                - dataset_results_str (str): Formatted dataset results for prompt injection
        - sources (list[str]): All source URLs collected
        - dataset_response (DatasetSearchResponse): Raw candidates for source-safe selection
        """
        project_title = requirements.get("project_title", "AI Project")
        project_type = requirements.get("project_type", "general")
        target_domain = requirements.get("target_domain", "")
        objectives = requirements.get("objectives", [])
        key_challenges = requirements.get("key_challenges", [])

        sources: list[str] = []

        # ── Web Search ──────────────────────────────────────────────────────
        web_query = self._build_web_query(
            project_title=project_title,
            project_type=project_type,
            domain=target_domain,
            objectives=objectives,
            challenges=key_challenges,
        )

        logger.info(f"Running web search: '{web_query}'")
        web_response: WebSearchResponse = web_search(web_query, max_results=max_web_results)
        web_results_str = web_response.to_formatted_string()
        sources.extend(web_response.get_sources())

        # ── Dataset Search ──────────────────────────────────────────────────
        logger.info(f"Running dataset search: type={project_type}, domain={target_domain}")
        dataset_response: DatasetSearchResponse = dataset_search(
            project_type=project_type,
            domain=target_domain,
            max_results=max_dataset_results,
            project_title=project_title,
            objectives=objectives,
        )
        dataset_results_str = dataset_response.to_formatted_string()

        # Add dataset source URLs
        for ds in dataset_response.datasets:
            if ds.source:
                sources.append(ds.source)

        logger.info(
            f"Search complete: {len(web_response.results)} web results, "
            f"{len(dataset_response.datasets)} datasets, "
            f"{len(sources)} total sources"
        )

        return web_results_str, dataset_results_str, sources, dataset_response

    @staticmethod
    def _build_web_query(
        project_title: str,
        project_type: str,
        domain: str,
        objectives: list[str],
        challenges: list[str],
    ) -> str:
        """
        Builds a focused web search query from the project requirements.

        Keeps the query concise (search engines perform better with shorter queries).
        """
        # Core: project type + domain
        type_str = project_type.replace("_", " ")
        parts = [f"{type_str} AI project"]

        if domain:
            parts.append(domain)

        # Add one key challenge if available — it's specific and useful
        if challenges:
            parts.append(challenges[0][:50])

        # Append "best practices" to get actionable results
        parts.append("best practices 2024")

        return " ".join(parts)


# Module-level singleton
search_service = SearchService()
