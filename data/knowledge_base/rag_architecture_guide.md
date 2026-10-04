# RAG (Retrieval-Augmented Generation): Architecture and Implementation Guide

## Overview

Retrieval-Augmented Generation (RAG) is a hybrid AI architecture that combines the parametric knowledge of a large language model (LLM) with non-parametric retrieval from an external knowledge base. RAG solves the hallucination problem and enables LLMs to answer questions grounded in specific, up-to-date documents.

## Core RAG Architecture

```
User Query
    |
    v
[Query Encoder] --> Query Embedding
    |
    v
[Vector Store] <-- Document Embeddings (indexed offline)
    |
    v
[Top-K Retrieved Chunks] (k=3-10 typically)
    |
    v
[Context + Query] --> [LLM] --> Grounded Answer
```

## Two-Phase Design

**Offline (Indexing) Phase**:
1. Load documents (PDF, TXT, HTML, Markdown)
2. Split into chunks (500-1000 tokens with 10-20% overlap)
3. Embed each chunk using a text embedding model
4. Store embeddings + metadata in a vector database

**Online (Retrieval) Phase**:
1. Embed the user query with the same embedding model
2. Perform approximate nearest neighbor (ANN) search in the vector DB
3. Retrieve top-k most relevant chunks
4. Inject retrieved chunks into the LLM prompt as context
5. Generate grounded response

## Document Chunking Strategies

The chunking strategy is one of the most important design decisions in RAG:

- **Fixed-size chunking**: Split every N tokens with M token overlap. Simple but may break semantic units. Good for homogeneous text.
- **Recursive character splitting**: Split by paragraph, then sentence, then character — preserves semantic units. Recommended for most use cases.
- **Semantic chunking**: Use sentence embeddings to split at semantic boundaries. Best quality, slower.
- **Document-aware chunking**: Respect document structure (headers, sections). Best for structured documents.

**Recommended settings**:
- Chunk size: 500-1000 tokens (1000-2000 characters)
- Chunk overlap: 100-200 tokens (10-20% of chunk size)
- Use metadata (source, page, section) to improve filtering

## Embedding Model Selection

| Model | Dimensions | Speed | Cost | Best For |
|-------|-----------|-------|------|----------|
| OpenAI text-embedding-3-small | 1536 | Fast | Low | General purpose, English |
| OpenAI text-embedding-3-large | 3072 | Medium | Medium | High accuracy tasks |
| Cohere embed-v3 | 1024 | Fast | Low | Multilingual |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | Very Fast | Free | Offline, privacy-sensitive |
| sentence-transformers/all-mpnet-base-v2 | 768 | Fast | Free | Higher accuracy offline |
| BGE-M3 | 1024 | Medium | Free | Multilingual, state-of-the-art |

## Vector Database Options

| Database | Type | Best For |
|----------|------|----------|
| ChromaDB | Embedded | Development, small datasets (<1M vectors) |
| Pinecone | Cloud | Production, managed, large scale |
| Weaviate | Self-hosted/Cloud | Complex filtering, multimodal |
| Qdrant | Self-hosted/Cloud | High performance, filtering |
| FAISS | Library | Research, offline, no server needed |
| pgvector | PostgreSQL extension | Existing Postgres infrastructure |

## Retrieval Strategies

**Sparse Retrieval (keyword-based)**:
- BM25, TF-IDF
- Good for exact matches, technical terminology
- Fast, no GPU needed

**Dense Retrieval (embedding-based)**:
- Semantic similarity via vector search
- Better for paraphrase, conceptual queries
- Requires embedding model

**Hybrid Retrieval** (recommended for production):
- Combine sparse + dense with Reciprocal Rank Fusion (RRF)
- Consistently outperforms either method alone

**Reranking** (optional but improves quality):
- After retrieval, use a cross-encoder reranker to re-score results
- Models: Cohere Rerank, BGE-Reranker, MS-MARCO cross-encoders
- Adds latency but significantly improves precision

## Advanced RAG Patterns

- **HyDE (Hypothetical Document Embeddings)**: Generate a hypothetical answer, embed it, then retrieve. Improves recall.
- **Multi-Query Retrieval**: Generate 3-5 query variants, retrieve for each, deduplicate. More robust.
- **Parent-Child Chunking**: Index small child chunks but retrieve parent chunks for more context.
- **Self-RAG**: LLM decides when to retrieve and validates retrieved content before using it.

## Evaluation Metrics for RAG

- **Retrieval**: Recall@K, Precision@K, MRR (Mean Reciprocal Rank), NDCG
- **Generation**: Faithfulness (is the answer grounded?), Answer Relevance, Context Precision
- **End-to-End**: RAGAS framework (automated RAG evaluation), human evaluation

## Key Datasets for RAG Benchmarking

- **MS MARCO**: 1M passages, real Bing queries — passage retrieval
- **Natural Questions**: Real Google queries with Wikipedia answers
- **TriviaQA**: 95K trivia questions with evidence documents
- **HotpotQA**: Multi-hop reasoning requiring multiple documents
- **BEIR**: 18 heterogeneous retrieval benchmarks

## Recommended Tech Stack

- **Document Loading**: LangChain document loaders (PDF, HTML, Markdown)
- **Text Splitting**: LangChain RecursiveCharacterTextSplitter
- **Embeddings**: OpenAI text-embedding-3-small or sentence-transformers
- **Vector Store**: ChromaDB (development), Pinecone/Qdrant (production)
- **LLM**: GPT-4o, Gemini 2.0 Flash, Claude 3.5 Sonnet
- **RAG Framework**: LangChain, LlamaIndex
- **Evaluation**: RAGAS, TruLens
