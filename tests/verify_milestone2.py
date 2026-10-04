"""
Milestone 2 verification: import all Pydantic models and LangGraph state,
then instantiate each one with sample data to confirm schema is valid.
"""

import sys
sys.path.insert(0, '.')

print("--- Milestone 2: Model + State Verification ---\n")

# 1. Requirements
from app.models.state_models import Requirements
req = Requirements(
    project_title="Defect Detection CV System",
    project_type="computer_vision",
    objectives=["Detect manufacturing defects with >95% accuracy"],
    target_domain="manufacturing",
    key_challenges=["Limited labeled data", "Real-time inference requirement"],
    complexity="medium",
    requires_rag=False,
    requires_real_time=True,
)
print(f"PASS  Requirements: {req.project_title} ({req.project_type})")

# 2. ResearchResult
from app.models.research_models import ResearchResult
res = ResearchResult(
    summary="YOLOv8 achieves state-of-the-art defect detection.",
    key_findings=["YOLOv8 achieves 98% mAP on MVTec AD", "Data augmentation critical"],
    dataset_hints=["MVTec AD", "DAGM dataset"],
    model_hints=["YOLOv8", "EfficientDet"],
    sources=["https://arxiv.org/abs/2304.00501"],
)
print(f"PASS  ResearchResult: {len(res.key_findings)} findings, {len(res.sources)} sources")

# 3. ArchitectureResult
from app.models.architecture_models import ArchitectureResult, DatasetStrategy, ModelStrategy, ComponentSpec
comp = ComponentSpec(name="Image Ingestion", role="Load images", technology="OpenCV")
arch = ArchitectureResult(
    project_type="computer_vision",
    system_overview="CNN-based defect detection pipeline.",
    components=[comp, ComponentSpec(name="Model Inference", role="Run YOLOv8", technology="PyTorch")],
    pipeline_steps=["Data Collection", "Preprocessing", "Training", "Inference"],
    tech_stack=["PyTorch", "YOLOv8", "FastAPI"],
    estimated_complexity="MEDIUM",
    deployment_approach="REST API with Docker",
)
print(f"PASS  ArchitectureResult: {len(arch.components)} components, {arch.estimated_complexity} complexity")

ds = DatasetStrategy(
    recommended_datasets=["MVTec AD"],
    data_collection_approach="Download from Kaggle",
    preprocessing_steps=["Resize to 640x640", "Normalize", "Augment"],
    estimated_data_size="5,000 images",
)
print(f"PASS  DatasetStrategy: {len(ds.recommended_datasets)} datasets")

ms = ModelStrategy(
    recommended_models=["YOLOv8n"],
    training_approach="fine-tune",
    training_approach_rationale="Pre-trained weights provide strong visual features.",
    evaluation_metrics=["mAP@0.5", "Precision", "Recall"],
    baseline_approach="Classic thresholding + blob detection",
    hardware_requirements="GPU with 8GB VRAM",
)
print(f"PASS  ModelStrategy: {ms.training_approach}, metrics: {ms.evaluation_metrics}")

# 4. CriticResult
from app.models.critic_models import CriticResult
critic = CriticResult(
    status="PASS",
    severity="LOW",
    issues=[],
    recommendations=["Consider adding a data validation step"],
    revision_target="none",
    reasoning="Architecture is sound and well-scoped.",
    feasibility_ok=True,
    requirements_covered=True,
    dataset_feasible=True,
    scope_realistic=True,
    no_contradictions=True,
)
print(f"PASS  CriticResult: status={critic.status}, severity={critic.severity}")

# 5. FinalProjectPlan
from app.models.report_models import FinalProjectPlan
plan = FinalProjectPlan(
    project_title="Defect Detection CV System",
    executive_summary="An automated system to detect manufacturing defects.",
    objectives=["Achieve >95% mAP on test set"],
    technical_architecture="YOLOv8-based pipeline...",
    dataset_plan="Use MVTec AD dataset...",
    model_plan="Fine-tune YOLOv8n...",
    implementation_roadmap=["Week 1: Data prep", "Week 2: Training", "Week 3: API"],
    success_metrics=["mAP@0.5 > 0.95"],
    estimated_timeline_weeks=4,
    revision_count=0,
    sources=["https://arxiv.org/abs/2304.00501"],
)
print(f"PASS  FinalProjectPlan: {plan.project_title}, {plan.estimated_timeline_weeks} weeks")

# 6. ProjectState
from app.graph.state import ProjectState, initial_state
state = initial_state("Build a defect detection system")
print(f"PASS  ProjectState: user_idea='{state['user_idea']}', revision_count={state['revision_count']}")

print("\nALL MILESTONE 2 CHECKS PASSED")
