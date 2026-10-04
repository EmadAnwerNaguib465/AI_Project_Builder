"""
app/tools/dataset_search.py

Dataset discovery tool for the Research Agent.

Two-layer strategy:
  1. Hugging Face Datasets API (free, no auth) — searches real HF hub
  2. Curated fallback — domain-specific dataset lists when HF API fails

Usage:
    from app.tools.dataset_search import dataset_search
    results = dataset_search(project_type="computer_vision", domain="manufacturing")
"""

import json
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.utils.logger import get_logger, log_tool_call

logger = get_logger(__name__)

# Hugging Face Datasets search endpoint (no API key required)
HF_DATASETS_API = "https://huggingface.co/api/datasets"
HF_SEARCH_TIMEOUT = 8.0  # seconds


# ---------------------------------------------------------------------------
# Curated fallback datasets per project type
# These are well-known, actually public datasets with verified sources.
# Used when the HF API is unavailable.
# ---------------------------------------------------------------------------
CURATED_DATASETS: dict[str, list[dict]] = {
    "computer_vision": [
        {"name": "ImageNet", "source": "https://www.image-net.org/", "description": "1.2M images, 1000 classes. Standard benchmark for image classification."},
        {"name": "COCO (Common Objects in Context)", "source": "https://cocodataset.org/", "description": "330K images with object detection, segmentation, and captioning annotations."},
        {"name": "MVTec AD", "source": "https://www.mvtec.com/company/research/datasets/mvtec-ad", "description": "5K industrial images for anomaly/defect detection across 15 categories."},
        {"name": "Open Images v7", "source": "https://storage.googleapis.com/openimages/web/index.html", "description": "9M images with labels, bounding boxes, and segmentation masks."},
        {"name": "CelebA", "source": "https://mmlab.ie.cuhk.edu.hk/projects/CelebA.html", "description": "200K celebrity face images with 40 attribute annotations."},
    ],
    "nlp": [
        {"name": "Hugging Face Datasets Hub", "source": "https://huggingface.co/datasets", "description": "Thousands of NLP datasets including GLUE, SuperGLUE, SQuAD, CoNLL."},
        {"name": "Common Crawl", "source": "https://commoncrawl.org/", "description": "Petabyte-scale web corpus for language model pretraining."},
        {"name": "SST-2 (Stanford Sentiment Treebank)", "source": "https://huggingface.co/datasets/sst2", "description": "67K movie review sentences for sentiment analysis (positive/negative)."},
        {"name": "SQuAD 2.0", "source": "https://rajpurkar.github.io/SQuAD-explorer/", "description": "150K Q&A pairs on Wikipedia articles for reading comprehension."},
        {"name": "AG News", "source": "https://huggingface.co/datasets/ag_news", "description": "120K news article snippets across 4 categories for text classification."},
    ],
    "rag": [
        {"name": "MS MARCO", "source": "https://microsoft.github.io/msmarco/", "description": "1M real Bing queries with passage-level answers for retrieval tasks."},
        {"name": "Natural Questions (NQ)", "source": "https://ai.google.com/research/NaturalQuestions", "description": "Real Google queries with Wikipedia-based answers for open-domain QA."},
        {"name": "TriviaQA", "source": "https://huggingface.co/datasets/trivia_qa", "description": "95K trivia Q&A pairs with evidence documents for RAG evaluation."},
        {"name": "BEIR Benchmark", "source": "https://github.com/beir-cellar/beir", "description": "18 retrieval benchmarks for evaluating dense and sparse retrieval systems."},
        {"name": "HotpotQA", "source": "https://hotpotqa.github.io/", "description": "113K multi-hop reasoning questions requiring information from 2+ documents."},
    ],
    "recommendation": [
        {"name": "MovieLens 25M", "source": "https://grouplens.org/datasets/movielens/", "description": "25M movie ratings from 162K users for collaborative filtering."},
        {"name": "Amazon Review Data", "source": "https://cseweb.ucsd.edu/~jmcauley/datasets/amazon_v2/", "description": "233M product reviews across 29 categories for recommendation research."},
        {"name": "Yelp Dataset", "source": "https://www.yelp.com/dataset", "description": "6.9M reviews from 150K businesses for business recommendation."},
        {"name": "Netflix Prize Dataset", "source": "https://www.kaggle.com/datasets/netflix-inc/netflix-prize-data", "description": "100M ratings from 480K users for matrix factorization."},
        {"name": "Book-Crossing Dataset", "source": "https://huggingface.co/datasets/mellahysf/book-crossings", "description": "1.1M ratings for 271K books from 278K users."},
    ],
    "multimodal": [
        {"name": "LAION-400M", "source": "https://laion.ai/laion-400-open-dataset/", "description": "400M image-text pairs for CLIP-style contrastive pretraining."},
        {"name": "Conceptual Captions (CC3M)", "source": "https://ai.google.com/research/ConceptualCaptions/", "description": "3M image-caption pairs harvested from the web."},
        {"name": "Visual Genome", "source": "https://visualgenome.org/", "description": "108K images with dense annotations of objects, attributes, and relationships."},
        {"name": "VQA v2", "source": "https://visualqa.org/", "description": "265K images with 1.1M questions for visual question answering."},
        {"name": "Flickr30k", "source": "https://huggingface.co/datasets/nlphuji/flickr30k", "description": "31K images with 5 caption annotations each for image-text matching."},
    ],
    "general": [
        {"name": "UCI Machine Learning Repository", "source": "https://archive.ics.uci.edu/", "description": "600+ datasets across tabular, time series, and classification tasks."},
        {"name": "Kaggle Datasets", "source": "https://www.kaggle.com/datasets", "description": "50K+ community datasets across all domains and task types."},
        {"name": "Papers With Code Datasets", "source": "https://paperswithcode.com/datasets", "description": "Benchmark datasets linked to state-of-the-art results and papers."},
        {"name": "OpenML", "source": "https://www.openml.org/search?type=data", "description": "4000+ curated ML datasets with metadata and benchmark results."},
    ],
}


@dataclass
class DatasetInfo:
    """Information about a single dataset."""
    name: str
    source: str
    description: str
    downloads: Optional[int] = None  # from HF API
    tags: list[str] = field(default_factory=list)


@dataclass
class DatasetSearchResponse:
    """Aggregated dataset search results."""
    query: str
    project_type: str
    datasets: list[DatasetInfo] = field(default_factory=list)
    source: str = "curated"   # "huggingface" or "curated"
    error: Optional[str] = None

    def to_formatted_string(self) -> str:
        """Formats datasets as a readable string for LLM consumption."""
        if not self.datasets:
            return f"No datasets found for '{self.query}' ({self.project_type})."

        lines = [
            f"Dataset Recommendations for: '{self.query}' [{self.project_type}]",
            f"Source: {self.source}\n",
        ]
        for i, d in enumerate(self.datasets, 1):
            lines.append(f"[{i}] {d.name}")
            lines.append(f"    Source: {d.source}")
            lines.append(f"    {d.description}")
            if d.tags:
                lines.append(f"    Tags: {', '.join(d.tags[:5])}")
            lines.append("")

        return "\n".join(lines)


def _search_huggingface(query: str, max_results: int = 5) -> list[DatasetInfo]:
    """
    Queries the Hugging Face Datasets API.
    Returns empty list on any failure — the curated fallback will be used.
    """
    try:
        params = {
            "search": query,
            "limit": max_results,
            "sort": "downloads",
            "direction": -1,
        }
        with httpx.Client(timeout=HF_SEARCH_TIMEOUT) as client:
            resp = client.get(HF_DATASETS_API, params=params)
            resp.raise_for_status()

        datasets = []
        for item in resp.json():
            datasets.append(DatasetInfo(
                name=item.get("id", "Unknown"),
                source=f"https://huggingface.co/datasets/{item.get('id', '')}",
                description=item.get("description", "No description available.")[:300],
                downloads=item.get("downloads"),
                tags=item.get("tags", [])[:10],
            ))

        logger.info(f"[TOOL]  dataset_search (HF API): {len(datasets)} results for '{query}'")
        return datasets

    except Exception as e:
        logger.warning(f"HuggingFace Datasets API failed: {e}. Using curated fallback.")
        return []


def dataset_search(
    project_type: str,
    domain: str = "",
    max_results: int = 5,
) -> DatasetSearchResponse:
    """
    Searches for relevant datasets for the given project type and domain.

    Strategy:
    1. Try the Hugging Face Datasets API with a combined query
    2. Fall back to the curated domain-specific list if HF fails or returns few results

    Args:
        project_type: AI project category (e.g., "computer_vision", "nlp", "rag")
        domain: Application domain to refine the search (e.g., "healthcare", "manufacturing")
        max_results: Maximum number of datasets to return

    Returns:
        DatasetSearchResponse with relevant dataset recommendations
    """
    # Normalize project type to a key we have curated data for
    pt = project_type.lower().replace(" ", "_")
    curated_key = pt if pt in CURATED_DATASETS else "general"

    # Build HF query
    query_parts = [project_type.replace("_", " ")]
    if domain:
        query_parts.append(domain)
    hf_query = " ".join(query_parts)

    log_tool_call(logger, "dataset_search", f"{project_type} | {domain}")

    # --- Try Hugging Face API first ---
    hf_results = _search_huggingface(hf_query, max_results=max_results)

    if len(hf_results) >= 3:
        return DatasetSearchResponse(
            query=hf_query,
            project_type=project_type,
            datasets=hf_results[:max_results],
            source="huggingface",
        )

    # --- Fall back to curated list ---
    curated = CURATED_DATASETS.get(curated_key, CURATED_DATASETS["general"])
    datasets = [
        DatasetInfo(name=d["name"], source=d["source"], description=d["description"])
        for d in curated[:max_results]
    ]

    # Merge HF results if we got any
    if hf_results:
        datasets = hf_results + datasets
        datasets = datasets[:max_results]

    return DatasetSearchResponse(
        query=hf_query,
        project_type=project_type,
        datasets=datasets,
        source="curated" if not hf_results else "mixed",
        error=None if hf_results else "HuggingFace API unavailable; using curated list.",
    )
