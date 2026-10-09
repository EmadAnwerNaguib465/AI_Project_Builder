"""
app/models/research_models.py

Pydantic model for the Research Agent's structured output.
Represents findings from web search and dataset discovery.
"""

from pydantic import BaseModel, Field
from app.models.dataset_models import DatasetSelection


class ResearchResult(BaseModel):
    """
    Structured research findings produced by the Research Agent.
    Aggregates web search results and dataset discovery into structured form.
    Consumed by the RAG Agent and Architect Agent.
    """

    dataset_selections: list[DatasetSelection] = Field(
        default_factory=list,
        description="Select up to five relevant dataset candidate IDs from tool results only. Empty if none fit.",
        max_length=5,
    )

    summary: str = Field(
        description="A concise 2-4 sentence summary of the research findings."
    )

    key_findings: list[str] = Field(
        description="The most important facts, trends, or techniques found during research.",
        min_length=1,
        max_length=10,
    )

    related_domains: list[str] = Field(
        description="Adjacent AI/ML fields or techniques relevant to this project.",
        default_factory=list,
    )

    challenges: list[str] = Field(
        description="Known technical or practical challenges identified during research.",
        default_factory=list,
    )

    dataset_hints: list[str] = Field(
        description="Names or descriptions of relevant public datasets found.",
        default_factory=list,
    )

    model_hints: list[str] = Field(
        description="Names or descriptions of relevant models, architectures, or APIs found.",
        default_factory=list,
    )

    recommended_approaches: list[str] = Field(
        description="Suggested approaches or methodologies based on current best practices.",
        default_factory=list,
    )

    sources: list[str] = Field(
        description="URLs or references used to compile this research.",
        default_factory=list,
    )
