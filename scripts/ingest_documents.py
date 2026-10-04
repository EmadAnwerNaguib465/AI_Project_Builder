"""
scripts/ingest_documents.py

CLI script to ingest knowledge base documents into ChromaDB.

Run this once before starting the application, and again whenever
you add new documents to data/knowledge_base/.

Usage:
    python scripts/ingest_documents.py

    # Force rebuild (re-embeds all documents even if store exists)
    python scripts/ingest_documents.py --force

Options:
    --force     Rebuild the vector store from scratch
    --dry-run   Show what would be ingested without doing it
    --verbose   Show detailed output

The script will:
1. Scan data/knowledge_base/ for .md, .txt, .pdf files
2. Load and chunk all documents
3. Embed with OpenAI (or sentence-transformers fallback)
4. Store in ChromaDB at data/chroma/
"""

import sys
import argparse
from pathlib import Path

# Add project root to path so we can import app modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import settings
from app.utils.logger import get_logger
from app.rag.loader import load_documents
from app.rag.splitter import split_documents
from app.rag.vectorstore import build_vectorstore, get_vector_count

logger = get_logger("ingest_documents")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents into the RAG knowledge base (ChromaDB)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild the vector store even if it already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without writing to ChromaDB.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  AI Project Builder — Knowledge Base Ingestion")
    print("=" * 60)
    print(f"\n  Knowledge Base: {settings.knowledge_base_path}")
    print(f"  ChromaDB:       {settings.chroma_persist_path}")
    print(f"  Chunk Size:     {settings.chunk_size} chars")
    print(f"  Chunk Overlap:  {settings.chunk_overlap} chars")
    print(f"  Embedding:      {settings.embedding_provider} / {settings.embedding_model}\n")

    # --- Check if already ingested ---
    if not args.force and not args.dry_run:
        existing_count = get_vector_count()
        if existing_count > 0:
            print(f"  ChromaDB already contains {existing_count} vectors.")
            print("  Use --force to rebuild from scratch.\n")
            print("  Ingestion skipped. Knowledge base is ready.")
            return 0

    # --- Step 1: Load documents ---
    print("Step 1: Loading documents...")
    documents = load_documents()

    if not documents:
        print("\n  [ERROR] No documents found in knowledge base directory.")
        print(f"  Expected location: {settings.knowledge_base_path}")
        print("  Supported formats: .md, .txt, .pdf")
        print("\n  The directory should already contain 5 seed documents.")
        print("  If empty, check that data/knowledge_base/ was populated correctly.")
        return 1

    print(f"  Loaded {len(documents)} document(s)")
    if args.verbose:
        for doc in documents:
            fname = doc.metadata.get("filename", "unknown")
            print(f"    - {fname} ({len(doc.page_content)} chars)")

    if args.dry_run:
        print("\n  [DRY RUN] Would split and embed the above documents.")
        print("  Re-run without --dry-run to perform ingestion.")
        return 0

    # --- Step 2: Split into chunks ---
    print("\nStep 2: Splitting documents into chunks...")
    chunks = split_documents(documents)
    print(f"  Split into {len(chunks)} chunks")

    if args.verbose:
        for i, chunk in enumerate(chunks[:5]):
            fname = chunk.metadata.get("filename", "?")
            print(f"    Chunk {i}: {fname} | {len(chunk.page_content)} chars")
        if len(chunks) > 5:
            print(f"    ... and {len(chunks) - 5} more chunks")

    # --- Step 3: Embed and store ---
    print("\nStep 3: Embedding and storing in ChromaDB...")
    print("  (This may take 30-120 seconds on first run...)")

    try:
        vectorstore = build_vectorstore(chunks)
        count = vectorstore._collection.count()
        print(f"\n  SUCCESS: {count} vectors stored in ChromaDB.")
        print(f"  Location: {settings.chroma_persist_path}")
        print("\n  Knowledge base is ready. You can now run the application:")
        print("  streamlit run app.py")
        return 0

    except Exception as e:
        print(f"\n  [ERROR] Ingestion failed: {type(e).__name__}: {e}")
        print("\n  Common causes:")
        print("  - Missing OPENAI_API_KEY (set it in .env or use local embeddings)")
        print("  - ChromaDB version incompatibility")
        print("  - Disk permissions issue")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
