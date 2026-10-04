"""
app/rag/loader.py

Document loader for the RAG knowledge base.
Supports: .md, .txt, .pdf files in the knowledge_base/ directory.

Uses langchain document loaders under the hood, returning a flat list
of LangChain Document objects ready for chunking.
"""

from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}


def load_documents(knowledge_base_dir: Optional[Path] = None) -> list[Document]:
    """
    Loads all supported documents from the knowledge base directory.

    Args:
        knowledge_base_dir: Path to the knowledge base directory.
                            Defaults to settings.knowledge_base_path.

    Returns:
        List of LangChain Document objects. Empty list if directory is
        empty or no supported files found (logged as a warning).
    """
    kb_path = knowledge_base_dir or settings.knowledge_base_path

    if not kb_path.exists():
        logger.warning(
            f"Knowledge base directory not found: {kb_path}\n"
            f"Run: python scripts/ingest_documents.py to set it up."
        )
        return []

    # Discover all supported files recursively
    all_files = []
    for ext in SUPPORTED_EXTENSIONS:
        all_files.extend(kb_path.rglob(f"*{ext}"))

    if not all_files:
        logger.warning(
            f"No supported documents found in {kb_path}. "
            f"Supported types: {SUPPORTED_EXTENSIONS}. "
            f"Run: python scripts/ingest_documents.py"
        )
        return []

    logger.info(f"Found {len(all_files)} documents in {kb_path}")

    documents = []
    failed = 0

    for file_path in sorted(all_files):
        try:
            docs = _load_single_file(file_path)
            documents.extend(docs)
            logger.info(f"  Loaded: {file_path.name} ({len(docs)} doc(s))")
        except Exception as e:
            logger.error(f"  Failed to load {file_path.name}: {e}")
            failed += 1

    logger.info(
        f"Document loading complete: {len(documents)} documents loaded, "
        f"{failed} failed."
    )
    return documents


def _load_single_file(file_path: Path) -> list[Document]:
    """
    Loads a single file and returns a list of Document objects.
    Adds source metadata to each document.
    """
    suffix = file_path.suffix.lower()

    if suffix in {".md", ".txt"}:
        return _load_text_file(file_path)
    elif suffix == ".pdf":
        return _load_pdf_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _load_text_file(file_path: Path) -> list[Document]:
    """Loads a plain text or markdown file."""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    return [Document(
        page_content=content,
        metadata={
            "source": str(file_path),
            "filename": file_path.name,
            "file_type": file_path.suffix.lstrip("."),
        }
    )]


def _load_pdf_file(file_path: Path) -> list[Document]:
    """Loads a PDF file using pypdfium2 via LangChain."""
    try:
        from langchain_community.document_loaders import PyPDFium2Loader
        loader = PyPDFium2Loader(str(file_path))
        docs = loader.load()
        # Add consistent metadata
        for doc in docs:
            doc.metadata["filename"] = file_path.name
            doc.metadata["file_type"] = "pdf"
        return docs
    except ImportError:
        # Fallback: try reading as text if pypdfium2 not available
        logger.warning(f"pypdfium2 not available; skipping PDF: {file_path.name}")
        return []
