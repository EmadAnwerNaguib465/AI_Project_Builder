"""
app/graph/state.py

LangGraph shared state definition for the AI Project Builder multi-agent system.

This TypedDict is the SINGLE source of truth passed between all agents.
Each agent reads only the fields it needs and writes only its own output fields.

State lifecycle:
  user_idea → [Supervisor] → requirements
           → [Research Agent] → research_results, sources
           → [RAG Agent] → retrieved_context
           → [Architect Agent] → architecture, dataset_strategy, model_strategy
           → [Critic Agent] → critic_feedback
           → [PASS] → [Report Agent] → final_report
           → [REVISE] → revision_count++ → relevant agent → Critic (loop)
"""

from typing import TypedDict, Optional, Any


class ProjectState(TypedDict, total=False):
    """
    Shared state passed between all LangGraph nodes.

    Fields marked with `total=False` are optional at any given graph step —
    they start as None/empty and get filled in as agents complete their work.

    Required at entry:
        user_idea (str): The raw project idea from the user.

    Populated by Supervisor:
        requirements (dict): Parsed Requirements model as dict.

    Populated by Research Agent:
        research_results (dict): ResearchResult model as dict.
        sources (list[str]): Accumulated source URLs.

    Populated by RAG Agent:
        retrieved_context (str): Relevant passages from the knowledge base.

    Populated by Architect Agent:
        architecture (dict): ArchitectureResult model as dict.
        dataset_strategy (dict): DatasetStrategy model as dict.
        model_strategy (dict): ModelStrategy model as dict.

    Populated by Critic Agent:
        critic_feedback (dict): CriticResult model as dict.

    Revision control:
        revision_count (int): Number of completed revision cycles (starts at 0).
        revision_target (str): "research" | "architect" | "none" — from critic.

    Populated by Report Agent:
        final_report (dict): FinalProjectPlan model as dict.

    Error handling:
        error (str | None): Set when a non-fatal error occurs in an agent.
                            Fatal errors raise exceptions instead.

    UI tracking:
        current_agent (str): Name of the agent currently executing (for Streamlit status).
    """

    # --- Entry point ---
    user_idea: str

    # --- Supervisor output ---
    requirements: dict[str, Any]

    # --- Research Agent output ---
    research_results: dict[str, Any]
    sources: list[str]

    # --- RAG Agent output ---
    retrieved_context: str

    # --- Architect Agent output ---
    architecture: dict[str, Any]
    dataset_strategy: dict[str, Any]
    model_strategy: dict[str, Any]

    # --- Critic Agent output ---
    critic_feedback: dict[str, Any]

    # --- Revision control ---
    revision_count: int
    revision_target: str  # "research" | "architect" | "none"

    # --- Report Agent output ---
    final_report: dict[str, Any]

    # --- Error handling ---
    error: Optional[str]

    # --- UI tracking ---
    current_agent: str


def initial_state(user_idea: str) -> ProjectState:
    """
    Returns the initial state for a new graph run.

    Args:
        user_idea: The raw project idea string from the user.

    Returns:
        A fully initialized ProjectState with all optional fields set to safe defaults.
    """
    return ProjectState(
        user_idea=user_idea,
        requirements={},
        research_results={},
        sources=[],
        retrieved_context="",
        architecture={},
        dataset_strategy={},
        model_strategy={},
        critic_feedback={},
        revision_count=0,
        revision_target="none",
        final_report={},
        error=None,
        current_agent="supervisor",
    )
