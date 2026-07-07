"""retrieval routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from app.api.routes import (
    local_retrieval_service,
)
from app.models.request_models import (
    RetrievalIndexRequest,
    RetrievalQueryRequest,
)

router = APIRouter()


# NOTE: /usage-ledger/* routes were extracted into app/api/usage_ledger_routes.py (services still live here).


# ----------------------------------------------------------------------
# v51.0 Local Retrieval Layer — local chunking + keyword retrieval.
# ----------------------------------------------------------------------
@router.get("/retrieval/summary")
def get_retrieval_summary(workspace_id: str | None = Query(default=None)) -> dict:
    return local_retrieval_service.summary(workspace_id)


@router.get("/retrieval/documents")
def list_retrieval_documents(workspace_id: str | None = Query(default=None)) -> dict:
    docs = local_retrieval_service.list_documents(workspace_id)
    return {"documents": docs, "count": len(docs)}


@router.post("/retrieval/documents")
def index_retrieval_document(request: RetrievalIndexRequest) -> dict:
    return local_retrieval_service.index_document(request.model_dump())


@router.post("/retrieval/query")
def query_retrieval(request: RetrievalQueryRequest) -> dict:
    return local_retrieval_service.query(request.model_dump())


# NOTE: /playbooks/* routes were extracted into app/api/playbooks_routes.py (services still live here).
