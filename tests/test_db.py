"""PostgreSQL tests. Need DATABASE_URL (any empty database); skipped otherwise."""
import os
import uuid
from datetime import datetime, timezone

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import api
from app.db import Store
from tests.conftest import generic_fake

pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")

META = {"split": "development", "agent_version": "v1", "prompt_version": "prompt-v1", "dataset_version": "d", "evaluator_version": "e",
        "fact_version": "f", "provider": "fake", "model": "m", "settings": {"k": 1}, "file_hashes": {"a": "b"},
        "source_revision": None, "created_at": datetime.now(timezone.utc)}


def claim(aid, s, e, label="unknown"):
    return {"claim_id": f"{aid}:{s}:{e}", "start_char": s, "end_char": e, "quote": "q", "label": label, "fact_ids": ["x.1"], "reason": "r"}


@pytest.fixture
def store():
    st = Store()
    st.init_schema()
    with st._conn() as c:
        c.execute("DELETE FROM runs")
    return st


def test_persist_success_empty_and_error_answers_with_joined_retrieval(store):
    rid = uuid.uuid4()
    store.create_run(rid, META)
    store.save_answer(rid, {"answer_id": "A02", "status": "ok", "claims": [], "latency_ms": 5})                       # valid empty
    store.save_answer(rid, {"answer_id": "A03", "status": "error", "error": {"type": "provider_timeout", "message": "t"}, "claims": []})
    store.save_answer(rid, {"answer_id": "A01", "status": "ok", "claims": [claim("A01", 50, 80), claim("A01", 0, 40)], "latency_ms": 9})
    store.finalize_run(rid, "completed", {"answers_scheduled": 3}, {"joint": None})
    run = store.get_run(rid)
    assert [a["answer_id"] for a in run["answers"]] == ["A01", "A02", "A03"]                     # stable answer order
    a1, a2, a3 = run["answers"]
    assert [c["start_char"] for c in a1["claims"]] == [0, 50]                                    # stable span order
    assert a2["status"] == "ok" and a2["claims"] == [] and a3["error"]["type"] == "provider_timeout" and a3["claims"] == []
    assert run["status"] == "completed" and run["settings"] == {"k": 1} and a1["claims"][0]["fact_ids"] == ["x.1"]


def test_unique_and_foreign_key_constraints(store):
    rid = uuid.uuid4()
    store.create_run(rid, META)
    store.save_answer(rid, {"answer_id": "A01", "status": "ok", "claims": [claim("A01", 0, 10)]})
    with pytest.raises(psycopg.errors.UniqueViolation):
        store.save_answer(rid, {"answer_id": "A01", "status": "ok", "claims": []})              # (run_id, answer_id)
    store.save_answer(rid, {"answer_id": "A02", "status": "ok", "claims": []})
    with pytest.raises(psycopg.errors.UniqueViolation):
        store.save_answer(rid, {"answer_id": "A03", "status": "ok", "claims": [claim("A03", 0, 10), claim("A03", 0, 10)]})
    with store._conn() as c, pytest.raises(psycopg.errors.ForeignKeyViolation):
        c.execute("INSERT INTO claim_results (run_id,answer_id,claim_id,start_char,end_char,quote,label,reason) "
                  "VALUES (%s,'NOPE','x',0,5,'q','unknown','r')", (rid,))


def test_label_check_constraint_rejects_bad_label(store):
    rid = uuid.uuid4()
    store.create_run(rid, META)
    with pytest.raises(psycopg.errors.CheckViolation):
        store.save_answer(rid, {"answer_id": "A01", "status": "ok", "claims": [claim("A01", 0, 10, "maybe")]})


@pytest.fixture
def client(store, settings):
    api.app.dependency_overrides[api.get_settings] = lambda: settings
    api.app.dependency_overrides[api.get_store_factory] = lambda: (lambda: store)
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_api_development_run_persists_scores_and_error_row(client, store):
    _p = generic_fake(fail_ids={"A02"}); api.app.dependency_overrides[api.get_provider_factory] = lambda: (lambda: _p)
    r = client.post("/evaluation-runs", json={"agent_version": "v1", "split": "development"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "completed" and body["counts"]["answers_scheduled"] == 40 and body["counts"]["answers_error"] == 1
    assert body["metrics"]["G"] == 376 and body["metrics"]["P"] == 39 and body["metrics"]["answer_error_count"] == 1
    run = client.get(f"/evaluation-runs/{body['run_id']}").json()
    assert len(run["answers"]) == 40 and run["answers"][1]["answer_id"] == "A02" and run["answers"][1]["error"]["type"] == "provider_timeout"
    assert run["answers"][1]["claims"] == [] and run["scores"]["missed_gold_ids"]
    assert all(a["claims"][0]["matched_gold"] is not None for a in run["answers"] if a["claims"])   # dev matches joined after save


def test_api_check_run_has_null_quality_everywhere(client, store):
    _p = generic_fake(); api.app.dependency_overrides[api.get_provider_factory] = lambda: (lambda: _p)
    r = client.post("/evaluation-runs", json={"agent_version": "v2", "split": "check"})
    assert r.status_code == 201
    m = r.json()["metrics"]
    assert r.json()["counts"]["answers_scheduled"] == 10 and m["P"] == 10
    assert m["G"] is None and m["M"] is None and m["C"] is None and m["joint"] is None and m["extraction"] is None
    run = client.get(f"/evaluation-runs/{r.json()['run_id']}").json()
    assert all(c["matched_gold"] is None and c["expected_label"] is None and c["label_correct"] is None
               for a in run["answers"] for c in a["claims"])


def test_get_run_404_and_422(client):
    assert client.get(f"/evaluation-runs/{uuid.uuid4()}").status_code == 404
    assert client.get("/evaluation-runs/not-a-uuid").status_code == 422


def test_post_run_422_for_bad_body(client):
    assert client.post("/evaluation-runs", json={"agent_version": "v9", "split": "development"}).status_code == 422
    assert client.post("/evaluation-runs", json={"agent_version": "v1", "split": "final"}).status_code == 422
