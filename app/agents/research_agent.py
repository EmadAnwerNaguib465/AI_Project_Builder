"""
app/agents/research_agent.py

Research Agent — second node in the multi-agent pipeline.

Responsibility:
    Gather research findings about the project from external sources
    (web search + dataset search) and synthesize them into a structured
    ResearchResult using the LLM.

Input  (from state): requirements (dict)
Output (to state):   research_results (dict), sources (list[str]), current_agent (str)

Tools used:
    - web_search  (via SearchService)
    - dataset_search (via SearchService)
"""

from app.graph.state import ProjectState
from app.models.research_models import ResearchResult
from app.models.state_models import Requirements
from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.utils.logger import get_logger, log_agent_start, log_agent_complete, log_error

logger = get_logger(__name__)


def run_research_agent(state: ProjectState) -> dict:
    """
    LangGraph node function for the Research Agent.

    Flow:
        1. Extract requirements from state
        2. Run web search + dataset search via SearchService
        3. Format all search results into the researcher prompt
        4. Call LLM with structured output → ResearchResult
        5. Return state update

    Args:
        state: The current ProjectState (must contain `requirements`).

    Returns:
        Partial state dict: research_results, sources, current_agent, error.
        On failure, sets error and returns safe empty values.
    """
    log_agent_start(logger, "Research Agent")

    # --- 1. Extract requirements ---
    requirements: dict = state.get("requirements", {})

    if not requirements:
        logger.error("Research Agent: requirements dict is empty. Supervisor may have failed.")
        return {
            "research_results": {},
            "sources": [],
            "current_agent": "research",
            "error": "Research Agent: missing requirements. Check Supervisor output.",
        }

    # Friendly aliases
    project_title = requirements.get("project_title", "AI Project")
    project_type = requirements.get("project_type", "general")
    target_domain = requirements.get("target_domain", "")
    objectives = requirements.get("objectives", [])
    key_challenges = requirements.get("key_challenges", [])
    complexity = requirements.get("complexity", "medium")

    logger.info(f"Researching: '{project_title}' ({project_type})")

    # --- 2. Run search tools ---
    try:
        web_results_str, dataset_results_str, tool_sources = search_service.run_research_search(
            requirements=requirements,
            max_web_results=5,
            max_dataset_results=5,
        )
    except Exception as e:
        log_error(logger, "Research Agent [search tools]", e)
        # Non-fatal: continue with empty search results
        web_results_str = "Web search failed. Using LLM training knowledge only."
        dataset_results_str = "Dataset search failed. Using LLM training knowledge only."
        tool_sources = []
        logger.warning("Proceeding with research using LLM knowledge only (no search results).")

    # --- 3. Build the research prompt ---
    try:
        prompt_template = llm_service.load_prompt("researcher")
        prompt = llm_service.format_prompt(
            prompt_template,
            project_title=project_title,
            project_type=project_type,
            target_domain=target_domain or "general",
            objectives="\n".join(f"- {o}" for o in objectives),
            key_challenges="\n".join(f"- {c}" for c in key_challenges),
            complexity=complexity,
            web_search_results=web_results_str,
            dataset_search_results=dataset_results_str,
        )
    except (FileNotFoundError, ValueError) as e:
        log_error(logger, "Research Agent [prompt]", e)
        return {
            "research_results": {},
            "sources": tool_sources,
            "current_agent": "research",
            "error": f"Research Agent prompt failed: {e}",
        }

    # --- 4. Call LLM for structured research synthesis ---
    try:
        research_result: ResearchResult = llm_service.invoke_structured(
            user_prompt=prompt,
            output_model=ResearchResult,
        )
        logger.info(
            f"Research complete: {len(research_result.key_findings)} findings, "
            f"{len(research_result.dataset_hints)} datasets, "
            f"{len(research_result.model_hints)} models"
        )
    except RuntimeError as e:
        log_error(logger, "Research Agent [LLM]", e)
        return {
            "research_results": {},
            "sources": tool_sources,
            "current_agent": "research",
            "error": f"Research Agent LLM call failed: {e}",
        }

    # --- 5. Merge sources (LLM-reported + tool-collected) ---
    all_sources = list(dict.fromkeys(
        research_result.sources + tool_sources
    ))  # deduplicated, order preserved

    log_agent_complete(logger, "Research Agent")

    return {
        "research_results": research_result.model_dump(),
        "sources": all_sources,
        "current_agent": "rag",
        "error": None,
    }
