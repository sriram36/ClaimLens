"""FastAPI service — thin HTTP wrapper around the agent and runner.

Routes do three things: validate the request, call the agent/runner/store,
and map internal errors to the right HTTP status codes.
"""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Literal

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .agent import ClaimsAgent
from .config import Settings
from .data import AgentInput, Catalogue, load_answers, load_gold
from .db import NotConfigured, Store
from .errors import AgentError, sanitize
from .providers import AzureProvider
from .runner import run_split

app = FastAPI(
    title="ClaimLens — Grounded Claim Extraction & Fact Verification Engine",
    description="Automated claim extraction and fact-checking against official brand product specifications.",
    version="1.0.0",
)


class ApiError(Exception):
    def __init__(self, status: int, type_: str, message: str):
        self.status = status
        self.type_ = type_
        self.message = sanitize(message)


@app.exception_handler(ApiError)
async def _api_error(_: Request, e: ApiError):
    return JSONResponse(
        status_code=e.status,
        content={"error": {"type": e.type_, "message": e.message}},
    )


# --------------------------------------------------------------------------
# Request / response models
# --------------------------------------------------------------------------

class ClassifyRequest(BaseModel):
    # extra="forbid" means gold fields (expected_label etc.) in the body -> 422
    model_config = ConfigDict(extra="forbid")
    answer_id: str = Field(min_length=1)
    brand_id: str = Field(min_length=1)
    question: str
    ai_answer: str = Field(min_length=1)
    agent_version: Literal["v1", "v2"]


class ClaimOut(BaseModel):
    claim_id: str
    start_char: int
    end_char: int
    quote: str
    label: Literal["supported", "contradicted", "unknown"]
    fact_ids: list[str]
    reason: str


class ClassifyResponse(BaseModel):
    answer_id: str
    claims: list[ClaimOut]


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_version: Literal["v1", "v2"]
    split: Literal["development", "check"]


# --------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------

@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache
def get_catalogue() -> Catalogue:
    return Catalogue.load(get_settings().data_dir / "brand_facts.csv")


# Provider and store are built lazily per-request so that validation errors
# (422) and unknown-brand (404) are never masked by a missing API key.
def get_provider_factory(settings: Settings = Depends(get_settings)):
    def make():
        try:
            return AzureProvider(
                deployment=settings.deployment,
                max_retries=settings.max_retries,
                temperature=settings.temperature,
            )
        except AgentError as e:
            raise ApiError(502, e.error_type, e.message)
    return make


def get_store_factory():
    def make() -> Store:
        try:
            return Store()
        except NotConfigured as e:
            raise ApiError(503, "database_not_configured", str(e))
    return make


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.post("/classify", response_model=ClassifyResponse)
def classify(
    req: ClassifyRequest,
    make_provider=Depends(get_provider_factory),
    catalogue: Catalogue = Depends(get_catalogue),
    settings: Settings = Depends(get_settings),
):
    if not catalogue.has_brand(req.brand_id):
        raise ApiError(404, "unknown_brand", f"unknown primary brand_id: {req.brand_id[:60]!r}")

    agent = ClaimsAgent(make_provider(), catalogue, req.agent_version, settings)
    try:
        res = agent.run(AgentInput(req.answer_id, req.brand_id, req.question, req.ai_answer))
    except AgentError as e:
        raise ApiError(e.http_status, e.error_type, e.message)

    return {"answer_id": res.answer_id, "claims": res.claims}


@app.post("/evaluation-runs", status_code=201)
def create_run(
    req: RunRequest,
    make_provider=Depends(get_provider_factory),
    catalogue: Catalogue = Depends(get_catalogue),
    settings: Settings = Depends(get_settings),
    make_store=Depends(get_store_factory),
):
    store = make_store()
    answers = load_answers(settings.data_dir / "answers.csv")
    gold = load_gold(settings.data_dir / "development_gold.csv")
    agent = ClaimsAgent(make_provider(), catalogue, req.agent_version, settings)
    try:
        report, _ = run_split(
            agent=agent, answers=answers, split=req.split,
            settings=settings, gold=gold, store=store,
        )
    except Exception as e:
        raise ApiError(500, "run_failed", f"{type(e).__name__}: {e}")

    return {
        "run_id": report["run_id"],
        "status": report["status"],
        "counts": report["counts"],
        "metrics": {
            k: report["metrics"][k]
            for k in ("quality_available", "G", "P", "M", "C", "extraction", "joint", "coverage", "answer_error_count")
        },
    }


@app.get("/evaluation-runs/{run_id}")
def get_run(run_id: uuid.UUID, make_store=Depends(get_store_factory)):
    run = make_store().get_run(run_id)
    if run is None:
        raise ApiError(404, "run_not_found", f"no run {run_id}")
    return run
