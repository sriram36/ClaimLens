"""PostgreSQL persistence (psycopg 3, parameterized SQL only)."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

SCHEMA = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


class NotConfigured(RuntimeError):
    pass


class Store:
    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DATABASE_URL")
        if not self.url:
            raise NotConfigured("DATABASE_URL is not set")

    def _conn(self):
        return psycopg.connect(self.url, row_factory=dict_row)

    def init_schema(self) -> None:
        with self._conn() as c:
            c.execute(SCHEMA.read_text(encoding="utf-8"))

    def create_run(self, run_id: uuid.UUID, meta: dict) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO runs (run_id, split, agent_version, prompt_version, dataset_version, evaluator_version,
                   fact_version, provider, model, settings, file_hashes, source_revision, status, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'running',%s)""",
                (run_id, meta["split"], meta["agent_version"], meta["prompt_version"], meta["dataset_version"],
                 meta["evaluator_version"], meta["fact_version"], meta["provider"], meta["model"],
                 Jsonb(meta["settings"]), Jsonb(meta["file_hashes"]), meta.get("source_revision"), meta["created_at"]))

    def save_answer(self, run_id: uuid.UUID, outcome: dict) -> None:
        """One terminal answer row (ok / empty / error) plus one claim row per accepted prediction, atomically."""
        err = outcome.get("error") or {}
        with self._conn() as c:
            c.execute(
                """INSERT INTO answer_results (run_id, answer_id, status, error_type, error_message, latency_ms, trace_ref, usage)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (run_id, outcome["answer_id"], outcome["status"], err.get("type"), err.get("message"),
                 outcome.get("latency_ms"), outcome.get("trace_ref"), Jsonb(outcome.get("usage") or {})))
            for cl in outcome.get("claims", []):
                c.execute(
                    """INSERT INTO claim_results (run_id, answer_id, claim_id, start_char, end_char, quote, label, fact_ids, reason)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (run_id, outcome["answer_id"], cl["claim_id"], cl["start_char"], cl["end_char"], cl["quote"],
                     cl["label"], Jsonb(cl["fact_ids"]), cl["reason"]))

    def update_matches(self, run_id: uuid.UUID, matches: list) -> None:
        """Development only; called after every prediction row is saved."""
        with self._conn() as c:
            for m in matches:
                c.execute(
                    """UPDATE claim_results SET matched_gold=%s, expected_label=%s, label_correct=%s
                       WHERE run_id=%s AND answer_id=%s AND start_char=%s AND end_char=%s""",
                    (m["matched_gold"], m["expected_label"], m["label_correct"], run_id, m["answer_id"],
                     m["start_char"], m["end_char"]))

    def finalize_run(self, run_id: uuid.UUID, status: str, counts: dict | None, scores: dict | None, error: dict | None = None):
        with self._conn() as c:
            c.execute("UPDATE runs SET status=%s, counts=%s, scores=%s, error=%s, finished_at=now() WHERE run_id=%s",
                      (status, Jsonb(counts), Jsonb(scores), Jsonb(error), run_id))

    def get_run(self, run_id: uuid.UUID) -> dict | None:
        """Joined retrieval: run metadata + answer outcomes (answer_id order) + claims (start_char order)."""
        with self._conn() as c:
            run = c.execute("SELECT * FROM runs WHERE run_id=%s", (run_id,)).fetchone()
            if run is None:
                return None
            rows = c.execute(
                """SELECT a.answer_id, a.status, a.error_type, a.error_message, a.latency_ms, a.trace_ref, a.usage,
                          cr.claim_id, cr.start_char, cr.end_char, cr.quote, cr.label, cr.fact_ids, cr.reason,
                          cr.matched_gold, cr.expected_label, cr.label_correct
                   FROM answer_results a
                   LEFT JOIN claim_results cr ON cr.run_id = a.run_id AND cr.answer_id = a.answer_id
                   WHERE a.run_id=%s ORDER BY a.answer_id, cr.start_char""", (run_id,)).fetchall()
        answers: dict = {}
        for r in rows:
            a = answers.setdefault(r["answer_id"], {
                "answer_id": r["answer_id"], "status": r["status"],
                "error": {"type": r["error_type"], "message": r["error_message"]} if r["error_type"] else None,
                "latency_ms": r["latency_ms"], "trace_ref": r["trace_ref"], "usage": r["usage"], "claims": []})
            if r["claim_id"] is not None:
                a["claims"].append({k: r[k] for k in ("claim_id", "start_char", "end_char", "quote", "label", "fact_ids",
                                                      "reason", "matched_gold", "expected_label", "label_correct")})
        out = {k: (str(v) if isinstance(v, uuid.UUID) else v.isoformat() if hasattr(v, "isoformat") else v)
               for k, v in run.items()}
        out["answers"] = list(answers.values())
        return out
