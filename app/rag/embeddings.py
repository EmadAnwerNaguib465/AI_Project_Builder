"""
app/rag/embeddings.py

Embedding model factory for the RAG pipeline.

Primary:  OpenAI text-embedding-3-small (requires OPENAI_API_KEY)
Fallback: sentence-transformers all-MiniLM-L6-v2 (local, free, no API key)

The fallback activates automatically if OPENAI_API_KEY is not set,
so the RAG pipeline works even without a paid API key.
"""

import os
from typing import Union

from langchain_core.embeddings import Embeddings

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_embedding_function() -> Embeddings:
    """
    Returns the configured embedding model as a LangChain Embeddings object.

    Selection logic:
    1. If OPENAI_API_KEY is set and embedding_provider == "openai"
       → OpenAI text-embedding-3-small
    2. Otherwise
       → sentence-transformers all-MiniLM-L6-v2 (local, free)

    Returns:
        A LangChain Embeddings instance compatible with ChromaDB.

    Raises:
        RuntimeError: If neither provider can be initialized.
    """
    if settings.openai_api_key and settings.embedding_provider == "openai":
        return _get_openai_embeddings()
    else:
        if not settings.openai_api_key:
            logger.warning(
                "OPENAI_API_KEY not set. "
                "Falling back to local sentence-transformers embeddings. "
                "Quality will be slightly lower than OpenAI embeddings."
            )
        return _get_local_embeddings()


def _get_openai_embeddings() -> Embeddings:
    """Returns OpenAI text-embedding-3-small."""
    try:
        from langchain_openai import OpenAIEmbeddings

        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,  # text-embedding-3-small
            openai_api_key=settings.openai_api_key,
        )
        logger.info(f"Embedding model: OpenAI {settings.embedding_model}")
        return embeddings

    except Exception as e:
        logger.error(f"Failed to initialize OpenAI embeddings: {e}. Falling back to local.")
        return _get_local_embeddings()


def _get_local_embeddings() -> Embeddings:
    """Returns sentence-transformers all-MiniLM-L6-v2 (local, no API key needed)."""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        model_name = "all-MiniLM-L6-v2"
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info(f"Embedding model: sentence-transformers/{model_name} (local)")
        return embeddings

    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize local embeddings: {e}\n"
            "Ensure sentence-transformers is installed: pip install sentence-transformers"
        ) from e
