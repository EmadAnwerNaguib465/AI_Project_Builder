"""
app/rag/splitter.py

Text chunking for the RAG pipeline.
Splits loaded Documents into smaller, overlapping chunks for embedding.

Uses LangChain's RecursiveCharacterTextSplitter which splits on:
  1. Double newlines (paragraphs)
  2. Single newlines
  3. Sentences
  4. Words
  5. Characters

This preserves semantic units better than fixed-size splitting.
"""

from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def split_documents(
    documents: list[Document],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[Document]:
    """
    Splits a list of Documents into smaller chunks suitable for embedding.

    Args:
        documents: Raw documents from the loader.
        chunk_size: Characters per chunk. Defaults to settings.chunk_size.
        chunk_overlap: Character overlap between chunks. Defaults to settings.chunk_overlap.

    Returns:
        List of chunked Document objects, each with preserved metadata
        plus `chunk_index` added.
    """
    if not documents:
        logger.warning("split_documents: received empty document list.")
        return []

    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Split priority: paragraph → sentence → word → character
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # Add chunk index to metadata for traceability
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    logger.info(
        f"Splitting complete: {len(documents)} documents -> {len(chunks)} chunks "
        f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
    )

    return chunks

