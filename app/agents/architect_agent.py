"""
app/agents/architect_agent.py

Architect Agent — fourth node in the multi-agent pipeline.

Responsibility:
    Design the complete technical architecture for the AI project.
    Produces three structured outputs consumed by the Critic and Report agents.

Input  (from state): requirements (dict), research_results (dict), retrieved_context (str)
Output (to state):   architecture (dict), dataset_strategy (dict), model_strategy (dict),
                     current_agent (str)

Tools used: None — the Architect only uses the LLM.
"""

import json

from app.graph.state import ProjectState
from app.models.architecture_models import ArchitectureResult, DatasetStrategy, ModelStrategy
from app.services.llm_service import llm_service
from app.utils.logger import get_logger, log_agent_start, log_agent_complete, log_error

logger = get_logger(__name__)


def run_architect_agent(state: ProjectState) -> dict:
    """
    LangGraph node function for the Architect Agent.

    Calls the LLM three times with structured output — once for each
    of the three design artifacts:
        1. ArchitectureResult  (system design + tech stack)
        2. DatasetStrategy     (data plan)
        3. ModelStrategy       (model selection + training plan)

    Each call uses the same rich prompt context so the three outputs
    are internally coherent.

    Args:
        state: The current ProjectState.

    Returns:
        Partial state dict: architecture, dataset_strategy, model_strategy,
        current_agent, error.
    """
    log_agent_start(logger, "Architect Agent")

    # --- 1. Unpack state ---
    requirements: dict = state.get("requirements", {})
    research_results: dict = state.get("research_results", {})
    retrieved_context: str = state.get("retrieved_context", "")

    if not requirements:
        logger.error("Architect Agent: requirements empty.")
        return {
            "architecture": {},
            "dataset_strategy": {},
            "model_strategy": {},
            "current_agent": "architect",
            "error": "Architect Agent: missing requirements.",
        }

    # Friendly aliases
    project_title = requirements.get("project_title", "AI Project")
    project_type = requirements.get("project_type", "general")
    target_domain = requirements.get("target_domain", "")
    objectives = requirements.get("objectives", [])
    constraints = requirements.get("constraints", [])
    key_challenges = requirements.get("key_challenges", [])
    complexity = requirements.get("complexity", "medium")
    requires_rag = requirements.get("requires_rag", False)
    requires_real_time = requirements.get("requires_real_time", False)

    research_summary = research_results.get("summary", "No research summary available.")
    dataset_hints = research_results.get("dataset_hints", [])
    model_hints = research_results.get("model_hints", [])

    logger.info(f"Designing architecture for: '{project_title}' ({project_type})")

    # --- 2. Build shared prompt context ---
    try:
        prompt_template = llm_service.load_prompt("architect")
        prompt_context = llm_service.format_prompt(
            prompt_template,
            project_title=project_title,
            project_type=project_type,
            target_domain=target_domain or "general",
            objectives="\n".join(f"- {o}" for o in objectives),
            constraints="\n".join(f"- {c}" for c in constraints) or "None specified",
            key_challenges="\n".join(f"- {c}" for c in key_challenges),
            complexity=complexity,
            requires_rag=str(requires_rag),
            requires_real_time=str(requires_real_time),
            research_summary=research_summary,
            dataset_hints="\n".join(f"- {d}" for d in dataset_hints) or "See research summary",
            model_hints="\n".join(f"- {m}" for m in model_hints) or "See research summary",
            retrieved_context=retrieved_context or "No knowledge base context available.",
        )
        prompt_context += (
            "\n\nSource-backed dataset recommendations:\n"
            + json.dumps(research_results.get("dataset_recommendations", []), ensure_ascii=False)
            + "\nUse these datasets only when appropriate. Do not invent dataset links or metadata. "
            "If none fit, propose collecting project-specific data. Benchmarks do not replace private RAG documents."
        )
    except (FileNotFoundError, ValueError) as e:
        log_error(logger, "Architect Agent [prompt]", e)
        return {
            "architecture": {},
            "dataset_strategy": {},
            "model_strategy": {},
            "current_agent": "architect",
            "error": f"Architect prompt failed: {e}",
        }

    # --- 3. Call LLM for ArchitectureResult ---
    try:
        logger.info("Generating system architecture...")
        architecture: ArchitectureResult = llm_service.invoke_structured(
            user_prompt=prompt_context + "\n\nFocus your response on the SYSTEM ARCHITECTURE (ArchitectureResult). Design the complete system.",
            output_model=ArchitectureResult,
        )
        logger.info(
            f"Architecture: {len(architecture.components)} components, "
            f"{len(architecture.tech_stack)} tech items, "
            f"complexity={architecture.estimated_complexity}"
        )
    except RuntimeError as e:
        log_error(logger, "Architect Agent [architecture]", e)
        return {
            "architecture": {},
            "dataset_strategy": {},
            "model_strategy": {},
            "current_agent": "architect",
            "error": f"Architecture design failed: {e}",
        }

    # --- 4. Call LLM for DatasetStrategy ---
    try:
        logger.info("Generating dataset strategy...")
        dataset_strategy: DatasetStrategy = llm_service.invoke_structured(
            user_prompt=prompt_context + "\n\nFocus your response on the DATASET STRATEGY (DatasetStrategy). Specify concrete datasets, preprocessing, and data collection.",
            output_model=DatasetStrategy,
        )
        logger.info(
            f"Dataset strategy: {len(dataset_strategy.recommended_datasets)} datasets, "
            f"{len(dataset_strategy.preprocessing_steps)} preprocessing steps"
        )
    except RuntimeError as e:
        log_error(logger, "Architect Agent [dataset]", e)
        return {
            "architecture": architecture.model_dump(),
            "dataset_strategy": {},
            "model_strategy": {},
            "current_agent": "architect",
            "error": f"Dataset strategy failed: {e}",
        }

    # --- 5. Call LLM for ModelStrategy ---
    try:
        logger.info("Generating model strategy...")
        model_strategy: ModelStrategy = llm_service.invoke_structured(
            user_prompt=prompt_context + "\n\nFocus your response on the MODEL STRATEGY (ModelStrategy). Specify models, training approach, metrics, and hardware needs.",
            output_model=ModelStrategy,
        )
        logger.info(
            f"Model strategy: {model_strategy.recommended_models}, "
            f"approach={model_strategy.training_approach}"
        )
    except RuntimeError as e:
        log_error(logger, "Architect Agent [model]", e)
        return {
            "architecture": architecture.model_dump(),
            "dataset_strategy": dataset_strategy.model_dump(),
            "model_strategy": {},
            "current_agent": "architect",
            "error": f"Model strategy failed: {e}",
        }

    log_agent_complete(logger, "Architect Agent")

    return {
        "architecture": architecture.model_dump(),
        "dataset_strategy": dataset_strategy.model_dump(),
        "model_strategy": model_strategy.model_dump(),
        "current_agent": "critic",
        "error": None,
    }
