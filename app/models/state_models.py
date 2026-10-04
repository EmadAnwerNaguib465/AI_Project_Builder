"""
app/models/state_models.py

Pydantic model for the Supervisor Agent's structured output.
Represents the parsed and validated project requirements extracted from the user's idea.
"""

from pydantic import BaseModel, Field
from typing import Literal


class Requirements(BaseModel):
    """
    Structured requirements extracted from the user's raw project idea.
    Produced by the Supervisor Agent, consumed by all downstream agents.
    """

    project_title: str = Field(
        description="A concise title for the proposed AI project."
    )

    project_type: Literal["computer_vision", "nlp", "rag", "recommendation", "multimodal", "general"] = Field(
        description="The primary AI/ML category of this project."
    )

    objectives: list[str] = Field(
        description="Clear, measurable objectives the project must achieve.",
        min_length=1,
        max_length=10,
    )

    target_domain: str = Field(
        description="The application domain (e.g., healthcare, e-commerce, education)."
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="Known limitations: budget, data availability, hardware, timeline, etc."
    )

    key_challenges: list[str] = Field(
        description="Anticipated technical challenges that must be addressed.",
        min_length=1,
    )

    complexity: Literal["simple", "medium", "complex"] = Field(
        description="Estimated project complexity based on scope and requirements."
    )

    requires_rag: bool = Field(
        default=False,
        description="True if the project explicitly requires a RAG component."
    )

    requires_real_time: bool = Field(
        default=False,
        description="True if the project requires real-time or low-latency inference."
    )
