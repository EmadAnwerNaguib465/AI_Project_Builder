"""
app/models/report_models.py

Pydantic model for the Report Agent's final structured output.
Represents the complete AI project plan delivered to the user.
"""

from pydantic import BaseModel, Field


class FinalProjectPlan(BaseModel):
    """
    The complete, validated AI project plan.
    Produced by the Report Agent after the Critic gives PASS.
    This is the primary output shown to the user in the Streamlit UI.
    """

    project_title: str = Field(
        description="The finalized title of the AI project."
    )

    executive_summary: str = Field(
        description="A 3-5 sentence non-technical summary of the project suitable for stakeholders."
    )

    objectives: list[str] = Field(
        description="Clear, measurable project objectives.",
        min_length=1,
    )

    technical_architecture: str = Field(
        description="Full description of the system architecture in markdown format."
    )

    dataset_plan: str = Field(
        description="Detailed dataset plan: what data, where to get it, how to process it."
    )

    model_plan: str = Field(
        description="Model selection rationale, training approach, and evaluation strategy."
    )

    implementation_roadmap: list[str] = Field(
        description="Step-by-step implementation plan in recommended order.",
        min_length=1,
    )

    risks_and_mitigations: list[str] = Field(
        description="Key risks with their corresponding mitigation strategies.",
        default_factory=list,
    )

    success_metrics: list[str] = Field(
        description="Quantitative or qualitative metrics to measure project success.",
        min_length=1,
    )

    estimated_timeline_weeks: int = Field(
        description="Estimated weeks needed to build an MVP of this project.",
        gt=0,
    )

    required_skills: list[str] = Field(
        description="Technical skills required to implement this project.",
        default_factory=list,
    )

    recommended_tools: list[str] = Field(
        description="Specific tools, APIs, and platforms recommended.",
        default_factory=list,
    )

    revision_count: int = Field(
        default=0,
        description="Number of critic revision cycles this plan went through.",
        ge=0,
    )

    sources: list[str] = Field(
        description="All references and sources used to compile this plan.",
        default_factory=list,
    )
