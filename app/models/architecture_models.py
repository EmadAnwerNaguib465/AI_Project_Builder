"""
app/models/architecture_models.py

Pydantic models for the Architect Agent's structured output.
Covers the full technical architecture, dataset strategy, and model strategy.
"""

from pydantic import BaseModel, Field
from typing import Literal


class ComponentSpec(BaseModel):
    """A single component in the system architecture."""

    name: str = Field(description="Component name (e.g., 'Data Ingestion Pipeline').")
    role: str = Field(description="What this component does in the system.")
    technology: str = Field(description="Recommended technology or library (e.g., 'Apache Kafka', 'FastAPI').")
    inputs: list[str] = Field(default_factory=list, description="What this component receives.")
    outputs: list[str] = Field(default_factory=list, description="What this component produces.")


class ArchitectureResult(BaseModel):
    """
    Complete technical architecture proposed by the Architect Agent.
    Describes the full system design: components, pipeline, and tech stack.
    """

    project_type: str = Field(
        description="AI/ML category of this project (confirmed or refined from requirements)."
    )

    system_overview: str = Field(
        description="2-4 sentence description of the overall system design."
    )

    components: list[ComponentSpec] = Field(
        description="List of major system components.",
        min_length=2,
    )

    pipeline_steps: list[str] = Field(
        description="Ordered end-to-end pipeline steps (e.g., ['Data Collection', 'Preprocessing', ...]).",
        min_length=2,
    )

    tech_stack: list[str] = Field(
        description="Full list of recommended technologies, frameworks, and libraries.",
        min_length=1,
    )

    estimated_complexity: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Overall complexity estimate for the architecture."
    )

    deployment_approach: str = Field(
        description="How the final system should be deployed (e.g., 'REST API with Docker', 'Streamlit app')."
    )

    scalability_notes: str = Field(
        default="",
        description="Notes on how the system can scale if needed."
    )


class DatasetStrategy(BaseModel):
    """
    Dataset plan proposed by the Architect Agent.
    Specifies what data to use, how to collect it, and how to prepare it.
    """

    recommended_datasets: list[str] = Field(
        description="Specific public datasets recommended for this project (with sources if known).",
        min_length=1,
    )

    data_collection_approach: str = Field(
        description="How to collect or obtain the data (e.g., 'Download from Hugging Face', 'Web scraping')."
    )

    preprocessing_steps: list[str] = Field(
        description="Required data preprocessing steps in order.",
        min_length=1,
    )

    estimated_data_size: str = Field(
        description="Rough estimate of data volume needed (e.g., '10,000 labeled images', '1M tokens')."
    )

    data_challenges: list[str] = Field(
        description="Potential data-related issues: imbalance, labeling cost, privacy, etc.",
        default_factory=list,
    )

    augmentation_strategy: str = Field(
        default="",
        description="Data augmentation or synthesis strategy if applicable."
    )


class ModelStrategy(BaseModel):
    """
    Model selection and training plan proposed by the Architect Agent.
    Specifies the ML approach, model choices, metrics, and hardware needs.
    """

    recommended_models: list[str] = Field(
        description="Specific model names or families recommended (e.g., 'YOLOv8', 'BERT-base', 'GPT-4o').",
        min_length=1,
    )

    training_approach: Literal["fine-tune", "zero-shot", "few-shot", "train-from-scratch", "api-only", "hybrid"] = Field(
        description="The primary model training/usage strategy."
    )

    training_approach_rationale: str = Field(
        description="Why this training approach is recommended for this specific project."
    )

    evaluation_metrics: list[str] = Field(
        description="Metrics to measure model performance (e.g., 'F1-score', 'mAP', 'BLEU', 'ROUGE-L').",
        min_length=1,
    )

    baseline_approach: str = Field(
        description="A simple baseline to compare against the proposed model."
    )

    hardware_requirements: str = Field(
        description="Minimum hardware needed (e.g., 'GPU with 8GB VRAM', 'CPU-only feasible')."
    )

    estimated_training_time: str = Field(
        default="",
        description="Rough training time estimate (e.g., '2-4 hours on a single GPU')."
    )
