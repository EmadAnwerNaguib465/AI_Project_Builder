"""
app/agents/supervisor.py

Supervisor Agent — the entry point of the multi-agent pipeline.

Responsibility:
    Read the user's raw project idea and extract structured, validated requirements
    that all downstream agents will use as their source of truth.

Input  (from state): user_idea (str)
Output (to state):   requirements (dict), current_agent (str)

Tools:  None — the Supervisor only uses the LLM.
"""

from app.graph.state import ProjectState
from app.models.state_models import Requirements
from app.services.llm_service import llm_service
from app.utils.logger import get_logger, log_agent_start, log_agent_complete, log_error
from app.utils.validators import validate_user_idea

logger = get_logger(__name__)


def run_supervisor(state: ProjectState) -> dict:
    """
    LangGraph node function for the Supervisor Agent.

    Reads `user_idea` from state, validates it, calls the LLM with
    structured output to produce a `Requirements` object, and returns
    the state update dict.

    Args:
        state: The current ProjectState (must contain `user_idea`).

    Returns:
        A partial state dict with keys: requirements, current_agent, error.
        On failure, sets error and returns empty requirements so the graph
        can handle it gracefully.
    """
    log_agent_start(logger, "Supervisor")

    # --- 1. Extract and validate the user idea ---
    user_idea = state.get("user_idea", "").strip()

    try:
        user_idea = validate_user_idea(user_idea)
    except ValueError as e:
        logger.error(f"Invalid user idea: {e}")
        return {
            "requirements": {},
            "current_agent": "supervisor",
            "error": f"Invalid input: {e}",
        }

    logger.info(f"Processing idea: '{user_idea[:80]}...'")

    # --- 2. Load and format the supervisor prompt ---
    try:
        prompt_template = llm_service.load_prompt("supervisor")
        prompt = llm_service.format_prompt(prompt_template, user_idea=user_idea)
    except (FileNotFoundError, ValueError) as e:
        log_error(logger, "Supervisor", e)
        return {
            "requirements": {},
            "current_agent": "supervisor",
            "error": f"Prompt loading failed: {e}",
        }

    # --- 3. Call the LLM with structured output ---
    try:
        requirements: Requirements = llm_service.invoke_structured(
            user_prompt=prompt,
            output_model=Requirements,
        )
        logger.info(
            f"Requirements extracted: title='{requirements.project_title}' "
            f"type='{requirements.project_type}' "
            f"complexity='{requirements.complexity}'"
        )
    except RuntimeError as e:
        log_error(logger, "Supervisor", e)
        return {
            "requirements": {},
            "current_agent": "supervisor",
            "error": f"LLM call failed in Supervisor: {e}",
        }

    # --- 4. Return state update ---
    log_agent_complete(logger, "Supervisor")

    return {
        "requirements": requirements.model_dump(),
        "current_agent": "research",
        "error": None,
    }
