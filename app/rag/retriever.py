"""
app/rag/retriever.py

Similarity search interface for the RAG pipeline.

Wraps the ChromaDB vector store with a clean retrieve() function
that returns formatted text chunks ready for LLM prompt injection.
Handles the case where the knowledge base is empty gracefully.
"""

from typing import Optional

from langchain_core.documents import Document

from app.config.settings import settings
from app.rag.vectorstore import load_vectorstore
from app.utils.logger import get_logger, log_tool_call

logger = get_logger(__name__)

# Module-level cached vector store (loaded once per process)
_vectorstore = None
_vectorstore_loaded = False


def _get_vectorstore():
    """Lazily loads and caches the ChromaDB vector store."""
    global _vectorstore, _vectorstore_loaded
    if not _vectorstore_loaded:
        _vectorstore = load_vectorstore()
        _vectorstore_loaded = True
    return _vectorstore


def retrieve(
    query: str,
    top_k: Optional[int] = None,
) -> tuple[list[Document], str]:
    """
    Retrieves the most relevant document chunks for a given query.

    Args:
        query: The search query (typically the project description or question).
        top_k: Number of chunks to retrieve. Defaults to settings.rag_top_k.

    Returns:
        Tuple of:
            - documents (list[Document]): Retrieved LangChain Document objects.
            - formatted_context (str): Formatted string of all retrieved passages,
              ready for direct insertion into an LLM prompt.

    Notes:
        - If the vector store is empty or not initialized, returns an empty list
          and a clear message — never raises.
        - Sources are preserved in document metadata.
    """
    top_k = top_k or settings.rag_top_k
    log_tool_call(logger, "rag_retriever", query)

    vectorstore = _get_vectorstore()

    # --- Handle empty/uninitialized vector store ---
    if vectorstore is None:
        msg = (
            "RAG knowledge base is not initialized. "
            "Run: python scripts/ingest_documents.py to set it up. "
            "Proceeding without retrieved context."
        )
        logger.warning(msg)
        return [], msg

    try:
        count = vectorstore._collection.count()
        if count == 0:
            msg = (
                "RAG knowledge base is empty (0 vectors). "
                "Run: python scripts/ingest_documents.py to ingest documents."
            )
            logger.warning(msg)
            return [], msg

        # Perform similarity search
        docs = vectorstore.similarity_search(query=query, k=top_k)
        logger.info(f"Retrieved {len(docs)} chunks for query: '{query[:60]}'")

        # Format retrieved chunks into a prompt-ready string
        formatted = _format_retrieved_docs(docs)
        return docs, formatted

    except Exception as e:
        logger.error(f"[ERR]   RAG retrieval failed: {e}")
        return [], f"RAG retrieval failed: {e}. Proceeding without context."


def retrieve_for_project(requirements: dict, top_k: Optional[int] = None) -> tuple[list[Document], str]:
    """
    Builds a project-specific query from requirements and retrieves relevant chunks.

    Args:
        requirements: The Requirements dict from state.
        top_k: Number of chunks to retrieve.

    Returns:
        Same as retrieve(): (documents, formatted_context)
    """
    project_type = requirements.get("project_type", "")
    domain = requirements.get("target_domain", "")
    objectives = requirements.get("objectives", [])

    # Build a descriptive query that captures the project's essence
    query_parts = [
        project_type.replace("_", " "),
        domain,
    ]
    if objectives:
        query_parts.append(objectives[0][:80])

    query = " ".join(p for p in query_parts if p)
    return retrieve(query, top_k=top_k)


def _format_retrieved_docs(docs: list[Document]) -> str:
    """
    Formats retrieved documents into a readable string for LLM prompt injection.

    Each chunk is presented with its source filename and content.
    """
    if not docs:
        return "No relevant passages retrieved from the knowledge base."

    lines = ["Retrieved Knowledge Base Passages:\n"]
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("filename", doc.metadata.get("source", "unknown"))
        lines.append(f"[Passage {i}] Source: {source}")
        lines.append(doc.page_content.strip())
        lines.append("")  # blank line between passages

    return "\n".join(lines)


def reset_cache() -> None:
    """Resets the module-level vector store cache (useful for testing)."""
    global _vectorstore, _vectorstore_loaded
    _vectorstore = None
    _vectorstore_loaded = False
