"""
app/agents/critic_agent.py

Critic Agent — fifth node in the multi-agent pipeline (quality gate).

Responsibility:
    Validate the architecture, dataset strategy, and model strategy.
    Produce a structured CriticResult that the graph's conditional edge
    uses to route: PASS -> report | REVISE -> research or architect.

Input  (from state): requirements, architecture, dataset_strategy, model_strategy,
                     revision_count
Output (to state):   critic_feedback (dict), revision_count (int),
                     revision_target (str), current_agent (str)
"""

from app.graph.state import ProjectState
from app.models.critic_models import CriticResult
from app.services.llm_service import llm_service
from app.utils.logger import (
    get_logger, log_agent_start, log_agent_complete,
    log_error, log_critic_result, log_routing,
)
from app.config.settings import settings

logger = get_logger(__name__)


def run_critic_agent(state: ProjectState) -> dict:
    """
    LangGraph node function for the Critic Agent.

    Validates the full technical plan and decides:
    - PASS  → route to report_agent
    - REVISE → route to revision_target (research or architect)

    Max revisions is read from settings.max_revisions (default: 2).
    If revision_count >= max_revisions, forces PASS regardless.

    Args:
        state: The current ProjectState.

    Returns:
        Partial state dict: critic_feedback, revision_count, revision_target,
        current_agent, error.
    """
    log_agent_start(logger, "Critic Agent")

    # --- 1. Unpack state ---
    requirements: dict = state.get("requirements", {})
    architecture: dict = state.get("architecture", {})
    dataset_strategy: dict = state.get("dataset_strategy", {})
    model_strategy: dict = state.get("model_strategy", {})
    revision_count: int = state.get("revision_count", 0)
    max_revisions: int = settings.max_revisions

    if not requirements or not architecture:
        logger.error("Critic Agent: missing requirements or architecture.")
        return {
            "critic_feedback": {},
            "revision_count": revision_count,
            "revision_target": "none",
            "current_agent": "critic",
            "error": "Critic Agent: prerequisites missing.",
        }

    project_title = requirements.get("project_title", "AI Project")
    logger.info(f"Evaluating plan for: '{project_title}' (revision {revision_count}/{max_revisions})")

    # --- 2. Build critic prompt ---
    try:
        prompt_template = llm_service.load_prompt("critic")

        # Format components list for readability
        components = architecture.get("components", [])
        components_str = "\n".join(
            f"  - {c.get('name', '?')}: {c.get('role', '?')} [{c.get('technology', '?')}]"
            for c in components
        )

        prompt = llm_service.format_prompt(
            prompt_template,
            project_title=project_title,
            project_type=requirements.get("project_type", "general"),
            objectives="\n".join(f"- {o}" for o in requirements.get("objectives", [])),
            constraints="\n".join(f"- {c}" for c in requirements.get("constraints", [])) or "None",
            complexity=requirements.get("complexity", "medium"),
            system_overview=architecture.get("system_overview", "Not specified"),
            components=components_str or "Not specified",
            tech_stack=", ".join(architecture.get("tech_stack", [])),
            estimated_complexity=architecture.get("estimated_complexity", "MEDIUM"),
            recommended_datasets=", ".join(dataset_strategy.get("recommended_datasets", [])),
            data_collection_approach=dataset_strategy.get("data_collection_approach", "Not specified"),
            estimated_data_size=dataset_strategy.get("estimated_data_size", "Not specified"),
            recommended_models=", ".join(model_strategy.get("recommended_models", [])),
            training_approach=model_strategy.get("training_approach", "Not specified"),
            evaluation_metrics=", ".join(model_strategy.get("evaluation_metrics", [])),
            hardware_requirements=model_strategy.get("hardware_requirements", "Not specified"),
            revision_count=str(revision_count),
            max_revisions=str(max_revisions),
        )
    except (FileNotFoundError, ValueError) as e:
        log_error(logger, "Critic Agent [prompt]", e)
        return {
            "critic_feedback": {},
            "revision_count": revision_count,
            "revision_target": "none",
            "current_agent": "critic",
            "error": f"Critic prompt failed: {e}",
        }

    # --- 3. Call LLM for structured critique ---
    try:
        critic_result: CriticResult = llm_service.invoke_structured(
            user_prompt=prompt,
            output_model=CriticResult,
        )
    except RuntimeError as e:
        log_error(logger, "Critic Agent [LLM]", e)
        # On LLM failure, force PASS to avoid infinite loop
        logger.warning("Critic LLM call failed — forcing PASS to avoid deadlock.")
        critic_result = CriticResult(
            status="PASS",
            severity="LOW",
            issues=[f"Critic evaluation failed: {e}"],
            recommendations=[],
            revision_target="none",
            reasoning="Forced PASS due to Critic LLM failure.",
        )

    # --- 4. Enforce max revisions ---
    if revision_count >= max_revisions and critic_result.status == "REVISE":
        logger.warning(
            f"Max revisions ({max_revisions}) reached. "
            f"Forcing PASS despite REVISE recommendation."
        )
        critic_result.status = "PASS"
        critic_result.revision_target = "none"
        critic_result.reasoning += f" [Forced PASS: max revisions ({max_revisions}) reached]"

    log_critic_result(logger, critic_result.status, critic_result.severity, revision_count)

    # --- 5. Determine routing ---
    if critic_result.status == "PASS":
        next_agent = "report"
        new_revision_count = revision_count  # don't increment on pass
        revision_target = "none"
    else:
        # REVISE
        revision_target = critic_result.revision_target
        new_revision_count = revision_count + 1
        next_agent = revision_target if revision_target in ("research", "architect") else "architect"

    log_routing(
        logger,
        "critic",
        next_agent,
        f"status={critic_result.status}, severity={critic_result.severity}",
    )

    log_agent_complete(logger, "Critic Agent")

    return {
        "critic_feedback": critic_result.model_dump(),
        "revision_count": new_revision_count,
        "revision_target": revision_target,
        "current_agent": next_agent,
        "error": None,
    }


def route_after_critic(state: ProjectState) -> str:
    """
    LangGraph conditional edge function called after the Critic Agent.

    Reads `current_agent` from state (set by run_critic_agent) and
    returns the name of the next graph node.

    Returns:
        "report"     → if critic said PASS
        "research"   → if critic said REVISE and target is research
        "architect"  → if critic said REVISE and target is architect
    """
    current = state.get("current_agent", "report")
    valid_routes = {"report", "research", "architect"}

    if current not in valid_routes:
        logger.warning(f"Unexpected routing target '{current}' — defaulting to 'report'")
        return "report"

    return current
