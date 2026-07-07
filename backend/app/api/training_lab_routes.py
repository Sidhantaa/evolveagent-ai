"""training-lab routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    training_lab_service,
)
from app.models.request_models import (
    TrainingComparisonRequest,
    TrainingDatasetCreateRequest,
    TrainingExampleCreateRequest,
    TrainingExampleUpdateRequest,
    TrainingRunCreateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v27.0 Private Training Lab (dataset preparation only — no auto-training)
# ----------------------------------------------------------------------
@router.get("/training-lab/dashboard")
def get_training_lab_dashboard() -> dict:
    return training_lab_service.dashboard()


@router.get("/training-lab/datasets")
def list_training_datasets() -> dict:
    datasets = training_lab_service.list_datasets()
    return {"datasets": datasets, "count": len(datasets)}


@router.post("/training-lab/datasets")
def create_training_dataset(request: TrainingDatasetCreateRequest) -> dict:
    return training_lab_service.create_dataset(request.model_dump())


@router.get("/training-lab/runs")
def list_training_runs() -> dict:
    runs = training_lab_service.list_runs()
    return {"runs": runs, "count": len(runs)}


@router.post("/training-lab/runs")
def create_training_run(request: TrainingRunCreateRequest) -> dict:
    return training_lab_service.create_run(request.model_dump())


@router.get("/training-lab/comparisons")
def list_training_comparisons() -> dict:
    comparisons = training_lab_service.list_comparisons()
    return {"comparisons": comparisons, "count": len(comparisons)}


@router.post("/training-lab/comparisons")
def create_training_comparison(request: TrainingComparisonRequest) -> dict:
    return training_lab_service.create_comparison(request.model_dump())


@router.patch("/training-lab/examples/{example_id}")
def update_training_example(example_id: str, request: TrainingExampleUpdateRequest) -> dict:
    try:
        return training_lab_service.update_example(example_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Example not found") from error


@router.get("/training-lab/datasets/{dataset_id}")
def get_training_dataset(dataset_id: str) -> dict:
    dataset = training_lab_service.get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    examples = training_lab_service.list_examples(dataset_id)
    return {"dataset": dataset, "examples": examples, "example_count": len(examples)}


@router.post("/training-lab/datasets/{dataset_id}/examples")
def add_training_example(dataset_id: str, request: TrainingExampleCreateRequest) -> dict:
    try:
        return training_lab_service.add_example(dataset_id, request.prompt, request.completion, request.approved)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Dataset not found") from error


@router.post("/training-lab/datasets/{dataset_id}/export")
def export_training_dataset(dataset_id: str) -> dict:
    try:
        return training_lab_service.export_dataset(dataset_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Dataset not found") from error
