"""
app/agents/rag_agent.py

RAG Agent — third node in the multi-agent pipeline.

Responsibility:
    Retrieve relevant passages from the ChromaDB knowledge base and
    synthesize them into a coherent context summary for the Architect Agent.

Input  (from state): requirements (dict), research_results (dict)
Output (to state):   retrieved_context (str), current_agent (str)

Tools used:
    - ChromaDB retriever (via app.rag.retriever)
"""

from app.graph.state import ProjectState
from app.services.llm_service import llm_service
from app.rag.retriever import retrieve_for_project
from app.utils.logger import get_logger, log_agent_start, log_agent_complete, log_error

logger = get_logger(__name__)


def run_rag_agent(state: ProjectState) -> dict:
    """
    LangGraph node function for the RAG Agent.

    Flow:
        1. Extract requirements from state
        2. Build a query and retrieve relevant chunks from ChromaDB
        3. If chunks found: call LLM to synthesize them into a context summary
        4. If no chunks: return a clear fallback message
        5. Return state update with retrieved_context

    Args:
        state: The current ProjectState.

    Returns:
        Partial state dict: retrieved_context, current_agent, error.
    """
    log_agent_start(logger, "RAG Agent")

    requirements: dict = state.get("requirements", {})
    research_results: dict = state.get("research_results", {})

    if not requirements:
        logger.warning("RAG Agent: requirements empty. Skipping RAG retrieval.")
        return {
            "retrieved_context": "No requirements available for RAG retrieval.",
            "current_agent": "architect",
            "error": None,
        }

    project_title = requirements.get("project_title", "AI Project")
    project_type = requirements.get("project_type", "general")
    objectives = requirements.get("objectives", [])

    logger.info(f"RAG retrieval for: '{project_title}'")

    # --- 1. Retrieve from ChromaDB ---
    try:
        docs, formatted_passages = retrieve_for_project(
            requirements=requirements,
            top_k=None,  # uses settings.rag_top_k
        )
        num_chunks = len(docs)
        logger.info(f"Retrieved {num_chunks} passages from knowledge base")
    except Exception as e:
        log_error(logger, "RAG Agent [retrieval]", e)
        docs = []
        formatted_passages = f"RAG retrieval error: {e}. Proceeding without context."
        num_chunks = 0

    # --- 2. If no chunks retrieved, skip LLM synthesis ---
    if num_chunks == 0:
        logger.warning("No relevant passages found. RAG Agent returning fallback context.")
        log_agent_complete(logger, "RAG Agent")
        return {
            "retrieved_context": formatted_passages,  # contains the warning message
            "current_agent": "architect",
            "error": None,
        }

    # --- 3. Synthesize retrieved passages with LLM ---
    try:
        prompt_template = llm_service.load_prompt("rag")
        prompt = llm_service.format_prompt(
            prompt_template,
            project_title=project_title,
            project_type=project_type,
            target_domain=requirements.get("target_domain", "general"),
            objectives="\n".join(f"- {o}" for o in objectives),
            retrieved_passages=formatted_passages,
            num_chunks=str(num_chunks),
            top_k=str(len(docs)),
        )

        synthesized_context = llm_service.invoke(user_prompt=prompt)
        logger.info(f"RAG synthesis complete: {len(synthesized_context)} chars")

    except Exception as e:
        log_error(logger, "RAG Agent [synthesis]", e)
        # Non-fatal: use raw retrieved passages instead of synthesis
        logger.warning("LLM synthesis failed; using raw retrieved passages as context.")
        synthesized_context = formatted_passages

    log_agent_complete(logger, "RAG Agent")

    return {
        "retrieved_context": synthesized_context,
        "current_agent": "architect",
        "error": None,
    }
