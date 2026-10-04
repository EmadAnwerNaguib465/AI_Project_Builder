"""
app/models/critic_models.py

Pydantic models for the Critic Agent's structured output.
The Critic validates the architecture and research, then returns a PASS or REVISE decision.
The graph's conditional edge routes based on CriticResult.status.
"""

from pydantic import BaseModel, Field
from typing import Literal


# Type aliases for the two key decision values
CriticStatus = Literal["PASS", "REVISE"]
Severity = Literal["LOW", "MEDIUM", "HIGH"]
RevisionTarget = Literal["research", "architect", "none"]


class CriticResult(BaseModel):
    """
    Structured validation result produced by the Critic Agent.

    The graph conditional edge reads `status` to decide routing:
    - "PASS"   → proceed to Report Agent
    - "REVISE" → route to `revision_target` agent for another pass

    If revision_count >= MAX_REVISIONS, the graph forces PASS regardless.
    """

    status: CriticStatus = Field(
        description="PASS if the plan is acceptable, REVISE if it needs improvement."
    )

    severity: Severity = Field(
        description=(
            "Severity of the identified issues. "
            "LOW = minor polish, MEDIUM = notable gaps, HIGH = fundamental problems."
        )
    )

    issues: list[str] = Field(
        description="Specific problems identified in the research or architecture.",
        default_factory=list,
    )

    recommendations: list[str] = Field(
        description="Actionable steps the target agent should take to address the issues.",
        default_factory=list,
    )

    revision_target: RevisionTarget = Field(
        default="none",
        description=(
            "Which agent should handle the revision: "
            "'research' if more information is needed, "
            "'architect' if the design needs to be reworked, "
            "'none' if status is PASS."
        )
    )

    reasoning: str = Field(
        description="Brief explanation of why this decision was made."
    )

    # Validation checklist — booleans for structured reporting
    feasibility_ok: bool = Field(
        default=True,
        description="Is the proposed architecture technically feasible?"
    )
    requirements_covered: bool = Field(
        default=True,
        description="Does the architecture address all stated requirements?"
    )
    dataset_feasible: bool = Field(
        default=True,
        description="Are the proposed datasets realistic and accessible?"
    )
    scope_realistic: bool = Field(
        default=True,
        description="Is the project scope realistic for the stated constraints?"
    )
    no_contradictions: bool = Field(
        default=True,
        description="Are there no internal contradictions in the plan?"
    )
