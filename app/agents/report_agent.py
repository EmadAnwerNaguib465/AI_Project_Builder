"""
app/agents/report_agent.py

Report Agent — final node in the multi-agent pipeline.

Responsibility:
    Synthesize ALL information from previous agents into a comprehensive,
    professional FinalProjectPlan and write it to state.

Input  (from state): all state fields
Output (to state):   final_report (dict), current_agent (str)
"""

from app.graph.state import ProjectState
from app.models.report_models import FinalProjectPlan
from app.services.llm_service import llm_service
from app.utils.logger import get_logger, log_agent_start, log_agent_complete, log_error

logger = get_logger(__name__)


def run_report_agent(state: ProjectState) -> dict:
    """
    LangGraph node function for the Report Agent.

    Pulls every field from state and synthesizes them into a FinalProjectPlan
    via structured LLM output.

    Args:
        state: The current ProjectState (all fields should be populated by now).

    Returns:
        Partial state dict: final_report, current_agent, error.
    """
    log_agent_start(logger, "Report Agent")

    # --- 1. Unpack all state fields ---
    requirements: dict = state.get("requirements", {})
    research_results: dict = state.get("research_results", {})
    retrieved_context: str = state.get("retrieved_context", "")
    architecture: dict = state.get("architecture", {})
    dataset_strategy: dict = state.get("dataset_strategy", {})
    model_strategy: dict = state.get("model_strategy", {})
    critic_feedback: dict = state.get("critic_feedback", {})
    sources: list = state.get("sources", [])
    revision_count: int = state.get("revision_count", 0)
    user_idea: str = state.get("user_idea", "")

    project_title = requirements.get("project_title", "AI Project")
    logger.info(f"Generating final report for: '{project_title}'")

    if not requirements or not architecture:
        logger.error("Report Agent: critical state fields missing.")
        return {
            "final_report": {},
            "current_agent": "report",
            "error": "Report Agent: missing requirements or architecture.",
        }

    # --- 2. Build report prompt ---
    try:
        prompt_template = llm_service.load_prompt("report")

        # Format components
        components = architecture.get("components", [])
        components_str = "\n".join(
            f"  - {c.get('name', '?')}: {c.get('role', '?')} [{c.get('technology', '?')}]"
            for c in components
        )

        # Format critic recommendations
        critic_recs = critic_feedback.get("recommendations", [])
        critic_recs_str = "\n".join(f"- {r}" for r in critic_recs) or "None"

        prompt = llm_service.format_prompt(
            prompt_template,
            user_idea=user_idea,
            project_title=project_title,
            project_type=requirements.get("project_type", "general"),
            target_domain=requirements.get("target_domain", "general"),
            objectives="\n".join(f"- {o}" for o in requirements.get("objectives", [])),
            constraints="\n".join(f"- {c}" for c in requirements.get("constraints", [])) or "None",
            complexity=requirements.get("complexity", "medium"),
            research_summary=research_results.get("summary", ""),
            dataset_hints="\n".join(f"- {d}" for d in research_results.get("dataset_hints", [])),
            model_hints="\n".join(f"- {m}" for m in research_results.get("model_hints", [])),
            retrieved_context=retrieved_context or "No knowledge base context.",
            system_overview=architecture.get("system_overview", ""),
            components=components_str,
            pipeline_steps="\n".join(f"- {s}" for s in architecture.get("pipeline_steps", [])),
            tech_stack=", ".join(architecture.get("tech_stack", [])),
            deployment_approach=architecture.get("deployment_approach", ""),
            recommended_datasets=", ".join(dataset_strategy.get("recommended_datasets", [])),
            data_collection_approach=dataset_strategy.get("data_collection_approach", ""),
            preprocessing_steps="\n".join(f"- {s}" for s in dataset_strategy.get("preprocessing_steps", [])),
            estimated_data_size=dataset_strategy.get("estimated_data_size", ""),
            augmentation_strategy=dataset_strategy.get("augmentation_strategy", "Not specified"),
            recommended_models=", ".join(model_strategy.get("recommended_models", [])),
            training_approach=model_strategy.get("training_approach", ""),
            training_rationale=model_strategy.get("training_approach_rationale", ""),
            evaluation_metrics=", ".join(model_strategy.get("evaluation_metrics", [])),
            baseline_approach=model_strategy.get("baseline_approach", ""),
            hardware_requirements=model_strategy.get("hardware_requirements", ""),
            revision_count=str(revision_count),
            critic_recommendations=critic_recs_str,
            sources="\n".join(f"- {s}" for s in sources[:20]) or "None collected",
        )
    except (FileNotFoundError, ValueError) as e:
        log_error(logger, "Report Agent [prompt]", e)
        return {
            "final_report": {},
            "current_agent": "report",
            "error": f"Report prompt failed: {e}",
        }

    # --- 3. Call LLM for FinalProjectPlan ---
    try:
        final_plan: FinalProjectPlan = llm_service.invoke_structured(
            user_prompt=prompt,
            output_model=FinalProjectPlan,
        )

        # Inject revision count from state (source of truth)
        final_plan.revision_count = revision_count

        # Merge sources
        if sources:
            all_sources = list(dict.fromkeys(final_plan.sources + sources))
            final_plan.sources = all_sources[:30]  # cap at 30

        logger.info(
            f"Final report generated: "
            f"{final_plan.estimated_timeline_weeks} weeks estimated, "
            f"{len(final_plan.implementation_roadmap)} roadmap steps, "
            f"{len(final_plan.sources)} sources"
        )

    except RuntimeError as e:
        log_error(logger, "Report Agent [LLM]", e)
        return {
            "final_report": {},
            "current_agent": "report",
            "error": f"Report generation failed: {e}",
        }

    log_agent_complete(logger, "Report Agent")

    return {
        "final_report": final_plan.model_dump(),
        "current_agent": "done",
        "error": None,
    }
