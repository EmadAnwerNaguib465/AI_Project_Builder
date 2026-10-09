"""
app/tools/web_search.py

Web search tool using the Tavily API.

Returns structured search results that the Research Agent synthesizes.
If TAVILY_API_KEY is not set, returns an empty result with a clear message
so the Research Agent can still operate using its training knowledge.

Usage:
    from app.tools.web_search import web_search
    results = web_search("YOLOv8 object detection best practices", max_results=5)
"""

from dataclasses import dataclass, field
from typing import Optional

from app.config.settings import settings
from app.utils.logger import get_logger, log_tool_call

logger = get_logger(__name__)


@dataclass
class WebSearchResult:
    """A single web search result."""
    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class WebSearchResponse:
    """Aggregated response from a web search query."""
    query: str
    results: list[WebSearchResult] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None

    def to_formatted_string(self) -> str:
        """
        Formats the search results as a readable string for LLM consumption.
        Each result is presented with its title, URL, and content snippet.
        """
        if not self.success or not self.results:
            return (
                f"Web search for '{self.query}' returned no results. "
                f"Reason: {self.error or 'No relevant results found.'}"
            )

        lines = [f"Web Search Results for: '{self.query}'\n"]
        for i, r in enumerate(self.results, 1):
            lines.append(f"[{i}] {r.title}")
            lines.append(f"    URL: {r.url}")
            lines.append(f"    {r.content[:400].strip()}")
            lines.append("")

        return "\n".join(lines)

    def get_sources(self) -> list[str]:
        """Returns list of source URLs from results."""
        return [r.url for r in self.results if r.url]


def web_search(query: str, max_results: int = 5, include_domains: Optional[list[str]] = None) -> WebSearchResponse:
    """
    Performs a web search using the Tavily API.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (1-10).

    Returns:
        WebSearchResponse with results, or error info if the search failed.
    """
    log_tool_call(logger, "web_search", query)

    # --- Check API key ---
    if not settings.tavily_api_key:
        logger.warning(
            "TAVILY_API_KEY is not set. Web search is disabled. "
            "The Research Agent will rely on LLM training knowledge."
        )
        return WebSearchResponse(
            query=query,
            results=[],
            success=False,
            error=(
                "Tavily API key not configured. "
                "Set TAVILY_API_KEY in .env to enable web search."
            ),
        )

    # --- Execute Tavily search ---
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)

        response = client.search(
            query=query,
            search_depth="basic",   # "basic" is faster; "advanced" is more thorough
            max_results=min(max_results, 10),
            include_answer=False,   # We want raw results for the LLM to synthesize
            include_domains=include_domains,
            timeout=20,
        )

        results = []
        for item in response.get("results", []):
            results.append(
                WebSearchResult(
                    title=item.get("title", "No title"),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                )
            )

        logger.info(f"[TOOL]  web_search: returned {len(results)} results for '{query[:60]}'")

        return WebSearchResponse(
            query=query,
            results=results,
            success=True,
        )

    except Exception as e:
        logger.error(f"[ERR]   web_search failed: {type(e).__name__}: {e}")
        return WebSearchResponse(
            query=query,
            results=[],
            success=False,
            error=f"Tavily search error: {type(e).__name__}: {e}",
        )
