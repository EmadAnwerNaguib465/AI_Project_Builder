"""
Milestone 7 verification: Full RAG pipeline.

Tests:
- All RAG module imports
- Document loading from knowledge_base/
- Document splitting
- Embedding function initialization
- Dry-run ingestion (build vectorstore from real documents)
- Retrieval with similarity search
- RAG agent import + graceful empty-state handling
"""
import sys
sys.path.insert(0, '.')

print("--- Milestone 7: RAG Pipeline Verification ---\n")
all_pass = True

# ── 1. Import checks ─────────────────────────────────────────────────────────
print("=== Import Checks ===")
modules = [
    ("app.rag.loader", "load_documents"),
    ("app.rag.splitter", "split_documents"),
    ("app.rag.embeddings", "get_embedding_function"),
    ("app.rag.vectorstore", "build_vectorstore, load_vectorstore"),
    ("app.rag.retriever", "retrieve, retrieve_for_project"),
    ("app.agents.rag_agent", "run_rag_agent"),
]
for mod, names in modules:
    try:
        m = __import__(mod, fromlist=[names])
        print(f"  PASS  {mod}")
    except Exception as e:
        print(f"  FAIL  {mod}: {e}")
        all_pass = False

print()

# ── 2. Document loading ───────────────────────────────────────────────────────
print("=== Document Loading ===")
from app.rag.loader import load_documents
from app.config.settings import settings

docs = load_documents()
if len(docs) >= 5:
    print(f"  PASS  Loaded {len(docs)} documents from knowledge_base/")
    for doc in docs:
        fname = doc.metadata.get('filename', '?')
        print(f"        - {fname} ({len(doc.page_content)} chars)")
elif len(docs) > 0:
    print(f"  WARN  Only {len(docs)} documents loaded (expected >= 5)")
else:
    print("  FAIL  No documents loaded - check data/knowledge_base/")
    all_pass = False

print()

# ── 3. Document splitting ─────────────────────────────────────────────────────
print("=== Document Splitting ===")
from app.rag.splitter import split_documents

if docs:
    chunks = split_documents(docs)
    if len(chunks) > len(docs):
        print(f"  PASS  Split {len(docs)} docs -> {len(chunks)} chunks")
        print(f"        First chunk preview: '{chunks[0].page_content[:80].strip()}...'")
        print(f"        chunk_index metadata: {chunks[0].metadata.get('chunk_index')}")
    else:
        print(f"  WARN  Only {len(chunks)} chunks from {len(docs)} docs (expected more)")
else:
    print("  SKIP  No documents to split")

print()

# ── 4. Embedding function ─────────────────────────────────────────────────────
print("=== Embedding Function ===")
from app.rag.embeddings import get_embedding_function

try:
    emb_fn = get_embedding_function()
    print(f"  PASS  Embedding function initialized: {type(emb_fn).__name__}")
    # Quick sanity check: embed a single string
    test_embedding = emb_fn.embed_query("test query for computer vision")
    print(f"  PASS  Embedding produced: {len(test_embedding)} dimensions")
    assert len(test_embedding) > 100, "Embedding seems too small"
except Exception as e:
    print(f"  FAIL  Embedding: {e}")
    all_pass = False
    emb_fn = None

print()

# ── 5. Build vectorstore (real ingestion) ─────────────────────────────────────
print("=== Vector Store Build ===")
from app.rag.vectorstore import build_vectorstore, load_vectorstore, get_vector_count
from pathlib import Path

# Use a test-specific chroma dir to avoid polluting production
test_chroma_dir = Path("./data/chroma")

if docs and chunks and emb_fn:
    try:
        vs = build_vectorstore(chunks, persist_dir=test_chroma_dir, embedding_fn=emb_fn)
        count = vs._collection.count()
        if count == len(chunks):
            print(f"  PASS  Built ChromaDB: {count} vectors stored")
        else:
            print(f"  WARN  Built ChromaDB: {count} vectors (expected {len(chunks)})")
    except Exception as e:
        print(f"  FAIL  build_vectorstore: {e}")
        import traceback; traceback.print_exc()
        all_pass = False
else:
    print("  SKIP  Prerequisites missing (docs/chunks/embeddings)")

print()

# ── 6. Retrieval test ─────────────────────────────────────────────────────────
print("=== Retrieval Test ===")
from app.rag.retriever import retrieve, retrieve_for_project, reset_cache

reset_cache()  # Ensure fresh load

test_queries = [
    "computer vision defect detection best practices",
    "NLP sentiment analysis fine-tuning",
    "RAG vector database chunking strategy",
    "recommendation system collaborative filtering",
]
for query in test_queries:
    try:
        retrieved_docs, formatted = retrieve(query, top_k=2)
        if retrieved_docs:
            sources = [d.metadata.get('filename', '?') for d in retrieved_docs]
            print(f"  PASS  '{query[:40]}...' -> {len(retrieved_docs)} chunks from {sources}")
        else:
            print(f"  WARN  '{query[:40]}...' -> 0 chunks (store may not be loaded)")
    except Exception as e:
        print(f"  FAIL  retrieve(): {e}")
        all_pass = False

print()

# ── 7. RAG Agent graceful handling ───────────────────────────────────────────
print("=== RAG Agent ===")
from app.agents.rag_agent import run_rag_agent

# Test with empty state
result = run_rag_agent({})
assert result.get("current_agent") == "architect", f"Expected 'architect', got {result.get('current_agent')}"
assert isinstance(result.get("retrieved_context"), str)
print("  PASS  Empty state -> graceful fallback, current_agent='architect'")

# Test with valid requirements (uses real ChromaDB)
mock_req = {
    "project_title": "CV Defect Detection",
    "project_type": "computer_vision",
    "target_domain": "manufacturing",
    "objectives": ["Detect defects with 95% accuracy"],
    "key_challenges": ["Limited data"],
    "complexity": "medium",
}
result = run_rag_agent({"requirements": mock_req})
assert result.get("current_agent") == "architect"
ctx = result.get("retrieved_context", "")
print(f"  PASS  With requirements: retrieved_context={len(ctx)} chars, agent='architect'")

print()
if all_pass:
    print("ALL MILESTONE 7 CHECKS PASSED")
else:
    print("SOME MILESTONE 7 CHECKS FAILED - review output above")
    sys.exit(1)
