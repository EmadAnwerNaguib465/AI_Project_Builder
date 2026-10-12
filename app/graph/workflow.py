"""
app/graph/workflow.py

LangGraph workflow — the complete multi-agent orchestration graph.

Graph topology:
    START
      |
      v
  [supervisor]        Parse requirements from user idea
      |
      v
  [research]          Web + dataset search → ResearchResult
      |
      v
  [rag]               ChromaDB retrieval → retrieved_context
      |
      v
  [architect]         Design architecture, dataset, model strategy
      |
      v
  [critic]            Validate plan → PASS or REVISE
      |
      +--PASS----------> [report] --> END
      |
      +--REVISE-------> [research] or [architect] (loops back)

Public API:
    from app.graph.workflow import run_pipeline, stream_pipeline

    # Blocking call — returns final state
    final_state = run_pipeline("Build a sentiment analysis chatbot")

    # Streaming — yields (agent_name, partial_state) tuples
    for agent, state in stream_pipeline("Build a sentiment analysis chatbot"):
        print(f"Agent {agent} completed")
"""

from typing import Generator
from uuid import UUID

from langgraph.graph import StateGraph, END

from app.graph.state import ProjectState, initial_state
from app.agents.supervisor import run_supervisor
from app.agents.research_agent import run_research_agent
from app.agents.rag_agent import run_rag_agent
from app.agents.architect_agent import run_architect_agent
from app.agents.critic_agent import run_critic_agent, route_after_critic
from app.agents.report_agent import run_report_agent
from app.utils.logger import get_logger
from app.services.tracing import configure_langsmith, pipeline_trace_config

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Graph node names — single source of truth
# ---------------------------------------------------------------------------
NODE_SUPERVISOR = "supervisor"
NODE_RESEARCH   = "research"
NODE_RAG        = "rag"
NODE_ARCHITECT  = "architect"
NODE_CRITIC     = "critic"
NODE_REPORT     = "report"


def build_graph() -> StateGraph:
    """
    Constructs and returns the compiled LangGraph StateGraph.

    This is called once at module import time. The compiled graph is
    cached as `app` at the module level.

    Returns:
        Compiled LangGraph app (CompiledGraph).
    """
    workflow = StateGraph(ProjectState)

    # ── Register all nodes ─────────────────────────────────────────────────
    workflow.add_node(NODE_SUPERVISOR, run_supervisor)
    workflow.add_node(NODE_RESEARCH,   run_research_agent)
    workflow.add_node(NODE_RAG,        run_rag_agent)
    workflow.add_node(NODE_ARCHITECT,  run_architect_agent)
    workflow.add_node(NODE_CRITIC,     run_critic_agent)
    workflow.add_node(NODE_REPORT,     run_report_agent)

    # ── Entry point ─────────────────────────────────────────────────────────
    workflow.set_entry_point(NODE_SUPERVISOR)

    # ── Linear edges ────────────────────────────────────────────────────────
    workflow.add_edge(NODE_SUPERVISOR, NODE_RESEARCH)
    workflow.add_edge(NODE_RESEARCH,   NODE_RAG)
    workflow.add_edge(NODE_RAG,        NODE_ARCHITECT)
    workflow.add_edge(NODE_ARCHITECT,  NODE_CRITIC)

    # ── Conditional edge: critic routes to report, research, or architect ───
    workflow.add_conditional_edges(
        NODE_CRITIC,
        route_after_critic,   # reads state["current_agent"] set by critic
        {
            "report":    NODE_REPORT,
            "research":  NODE_RESEARCH,   # ← revision loop back
            "architect": NODE_ARCHITECT,  # ← revision loop back
        },
    )

    # ── Terminal edge ────────────────────────────────────────────────────────
    workflow.add_edge(NODE_REPORT, END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# Module-level compiled graph (import and use directly)
# ---------------------------------------------------------------------------
graph = build_graph()
logger.info("LangGraph workflow compiled successfully")


# ---------------------------------------------------------------------------
# Public pipeline API
# ---------------------------------------------------------------------------

def run_pipeline(user_idea: str) -> ProjectState:
    """
    Runs the complete multi-agent pipeline synchronously.

    Args:
        user_idea: The raw project idea string from the user.

    Returns:
        The final ProjectState after all agents have completed.
        Check state["error"] and state["final_report"] for results.

    Raises:
        ValueError: If user_idea is empty.
        RuntimeError: On unrecoverable graph execution errors.
    """
    if not user_idea or not user_idea.strip():
        raise ValueError("user_idea cannot be empty.")

    logger.info(f"Pipeline START: '{user_idea[:80]}'")

    state = initial_state(user_idea)

    try:
        final_state: ProjectState = graph.invoke(state)
        logger.info(
            f"Pipeline COMPLETE: "
            f"revision_count={final_state.get('revision_count', 0)}, "
            f"has_report={bool(final_state.get('final_report'))}, "
            f"error={final_state.get('error')}"
        )
        return final_state

    except Exception as e:
        logger.error(f"Pipeline FAILED: {type(e).__name__}: {e}")
        raise RuntimeError(f"Pipeline execution failed: {e}") from e


def stream_pipeline(
    user_idea: str,
    run_id: UUID | None = None,
) -> Generator[tuple[str, ProjectState], None, None]:
    """
    Runs the pipeline in streaming mode, yielding after each agent completes.

    Designed for real-time Streamlit UI updates.

    Args:
        user_idea: The raw project idea string from the user.

    Yields:
        Tuples of (agent_name: str, state: ProjectState) after each node.
        The final yield has agent_name="__end__" with the complete state.

    Example:
        for agent, state in stream_pipeline("Build a chatbot"):
            update_ui(agent, state)
    """
    if not user_idea or not user_idea.strip():
        raise ValueError("user_idea cannot be empty.")

    logger.info(f"Pipeline STREAM START: '{user_idea[:80]}'")
    state = initial_state(user_idea)

    try:
        configure_langsmith()
        trace_config = pipeline_trace_config(run_id)
        for chunk in graph.stream(state, stream_mode="updates", config=trace_config):
            # chunk is a dict: {node_name: state_update}
            for node_name, state_update in chunk.items():
                logger.info(f"Stream: node '{node_name}' completed")
                yield node_name, state_update

        logger.info("Pipeline STREAM COMPLETE")

    except Exception as e:
        logger.error(f"Pipeline STREAM FAILED: {type(e).__name__}: {e}")
        raise RuntimeError(f"Streaming pipeline failed: {e}") from e


def get_graph_info() -> dict:
    """
    Returns metadata about the compiled graph for display/debugging.

    Returns:
        Dict with nodes, entry_point, and edge structure.
    """
    return {
        "nodes": [
            NODE_SUPERVISOR,
            NODE_RESEARCH,
            NODE_RAG,
            NODE_ARCHITECT,
            NODE_CRITIC,
            NODE_REPORT,
        ],
        "entry_point": NODE_SUPERVISOR,
        "terminal_node": NODE_REPORT,
        "conditional_edge": {
            "from": NODE_CRITIC,
            "routes": {
                "PASS":          NODE_REPORT,
                "REVISE(research)":  NODE_RESEARCH,
                "REVISE(architect)": NODE_ARCHITECT,
            },
        },
        "max_revisions": __import__("app.config.settings", fromlist=["settings"]).settings.max_revisions,
    }
