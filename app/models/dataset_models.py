"""Dataset selections reference tool results, never model-generated URLs."""

from pydantic import BaseModel, Field


class DatasetSelection(BaseModel):
    candidate_id: str = Field(description="Exact candidate ID from dataset search, e.g. dataset-1.")
    relevance: str = Field(description="Why this dataset fits the project, including limitations or domain mismatch.", max_length=1200)


class DatasetRecommendation(BaseModel):
    name: str
    url: str
    description: str
    relevance: str
    provider: str
    discovery_source: str
    data_type: str | None = None
    size: str | None = None
    license: str | None = None
    access: str | None = None
