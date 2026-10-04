"""
app/rag/vectorstore.py

ChromaDB vector store manager for the RAG pipeline.

Handles:
- Creating and persisting the ChromaDB collection
- Adding document chunks with their embeddings
- Returning a retriever interface for similarity search

The vector store persists to data/chroma/ so embeddings are computed
only once during ingestion, not at query time.
"""

from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma

from app.config.settings import settings
from app.rag.embeddings import get_embedding_function
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Fixed collection name — all documents go into one collection
COLLECTION_NAME = "ai_project_knowledge"


def build_vectorstore(
    chunks: list[Document],
    persist_dir: Optional[Path] = None,
    embedding_fn: Optional[Embeddings] = None,
) -> Chroma:
    """
    Builds (or rebuilds) the ChromaDB vector store from document chunks.

    This is called by the ingest script, not at query time.
    Replaces the existing collection if it exists.

    Args:
        chunks: List of chunked Document objects from the splitter.
        persist_dir: Directory to persist ChromaDB. Defaults to settings.chroma_persist_path.
        embedding_fn: Embedding function. Defaults to get_embedding_function().

    Returns:
        Initialized Chroma vector store.

    Raises:
        ValueError: If chunks list is empty.
        RuntimeError: If ChromaDB initialization fails.
    """
    if not chunks:
        raise ValueError(
            "Cannot build vector store with empty chunks list. "
            "Load and split documents first."
        )

    persist_dir = persist_dir or settings.chroma_persist_path
    persist_dir.mkdir(parents=True, exist_ok=True)

    embedding_fn = embedding_fn or get_embedding_function()

    logger.info(
        f"Building ChromaDB vector store: {len(chunks)} chunks -> {persist_dir}"
    )

    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_fn,
            collection_name=COLLECTION_NAME,
            persist_directory=str(persist_dir),
        )
        logger.info(
            f"Vector store built: {vectorstore._collection.count()} vectors stored "
            f"in collection '{COLLECTION_NAME}'"
        )
        return vectorstore

    except Exception as e:
        raise RuntimeError(
            f"Failed to build ChromaDB vector store: {e}"
        ) from e


def load_vectorstore(
    persist_dir: Optional[Path] = None,
    embedding_fn: Optional[Embeddings] = None,
) -> Optional[Chroma]:
    """
    Loads an existing ChromaDB vector store from disk.

    Args:
        persist_dir: ChromaDB persistence directory. Defaults to settings.chroma_persist_path.
        embedding_fn: Embedding function. Must match the one used during ingestion.

    Returns:
        Chroma vector store, or None if no store exists yet.
    """
    persist_dir = persist_dir or settings.chroma_persist_path

    if not persist_dir.exists():
        logger.warning(
            f"ChromaDB directory not found: {persist_dir}. "
            "Run: python scripts/ingest_documents.py to create it."
        )
        return None

    # Check if there's anything actually in the directory
    if not any(persist_dir.iterdir()):
        logger.warning(
            f"ChromaDB directory is empty: {persist_dir}. "
            "Run: python scripts/ingest_documents.py"
        )
        return None

    try:
        embedding_fn = embedding_fn or get_embedding_function()
        vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            persist_directory=str(persist_dir),
        )
        count = vectorstore._collection.count()
        logger.info(f"ChromaDB loaded: {count} vectors in '{COLLECTION_NAME}'")
        return vectorstore

    except Exception as e:
        logger.error(f"Failed to load ChromaDB: {e}")
        return None


def get_vector_count(persist_dir: Optional[Path] = None) -> int:
    """Returns the number of vectors in the store, or 0 if not initialized."""
    try:
        vs = load_vectorstore(persist_dir)
        if vs is None:
            return 0
        return vs._collection.count()
    except Exception:
        return 0
