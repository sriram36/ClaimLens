"""Sequential evaluation runner: runs the agent over a split, saves predictions, THEN joins gold and scores."""
from __future__ import annotations

import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .agent import ClaimsAgent
from .config import ROOT, Settings
from .data import AgentInput, Answer, GoldClaim, file_hashes
from .errors import AgentError
from .scoring import error_analysis, score_run
from .versions import DATASET_VERSION, EVALUATOR_VERSION, FACT_VERSION


def source_revision() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              timeout=5, check=True).stdout.strip() or None
    except Exception:
        return None


def run_meta(agent: ClaimsAgent, split: str, settings: Settings) -> dict:
    return {
        "split": split,
        "agent_version": agent.version,
        "prompt_version": agent.prompt_version,
        "dataset_version": DATASET_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "fact_version": FACT_VERSION,
        "provider": agent.provider.name,
        "model": agent.provider.model,   # deployment name for Azure
        "settings": settings.public(),
        "file_hashes": file_hashes(settings.data_dir),
        "source_revision": source_revision(),
        "created_at": datetime.now(timezone.utc),
    }


def run_split(*, agent: ClaimsAgent, answers: list[Answer], split: str, settings: Settings,
              gold: list[GoldClaim] | None = None, store=None, progress=None, limit: int | None = None):
    """Returns (report, exchanges). Quality metrics are computed for 'development' only; 'check' stays null."""
    scheduled = sorted([a for a in answers if a.split == split], key=lambda a: a.answer_id)
    if limit:
        scheduled = scheduled[:limit]
    run_id = uuid.uuid4()
    meta = run_meta(agent, split, settings)
    if store:
        store.create_run(run_id, meta)
    outcomes, exchanges = [], []
    t_run = time.perf_counter()
    try:
        for n, a in enumerate(scheduled, 1):
            t0 = time.perf_counter()
            outcome = {"answer_id": a.answer_id, "status": "ok", "claims": [], "error": None, "usage": {}, "turns": 0}
            trace = []
            try:
                res = agent.run(AgentInput.from_answer(a))
                outcome.update(claims=res.claims, usage=res.usage, turns=res.turns)
                trace = res.trace
            except AgentError as e:      # answer-level error: preserved, no accepted predictions, never "unknown"
                outcome.update(status="error", claims=[], error=e.as_dict())
            outcome["latency_ms"] = int((time.perf_counter() - t0) * 1000)
            outcome["trace_ref"] = f"exchanges/{a.answer_id}"
            outcomes.append(outcome)
            exchanges.append({"answer_id": a.answer_id, "status": outcome["status"], "error": outcome["error"], "trace": trace})
            if store:
                store.save_answer(run_id, outcome)
            if progress:
                progress(n, len(scheduled), outcome)
        ids = [a.answer_id for a in scheduled]
        score = score_run(split, ids, outcomes, gold if split == "development" else None)
        analysis = None
        if score["quality_available"]:
            preds = {c["claim_id"]: c for o in outcomes for c in o["claims"]}
            analysis = error_analysis([g for g in gold if g.answer_id in set(ids)], preds, score)
            if store:
                store.update_matches(run_id, score["matches"])
            claim_match = {(m["answer_id"], m["start_char"], m["end_char"]): m for m in score["matches"]}
            for o in outcomes:
                for c in o["claims"]:
                    m = claim_match[(o["answer_id"], c["start_char"], c["end_char"])]
                    c.update(matched_gold=m["matched_gold"], expected_label=m["expected_label"], label_correct=m["label_correct"])
        counts = {"answers_scheduled": len(ids), "answers_ok": sum(o["status"] == "ok" for o in outcomes),
                  "answers_error": score["answer_error_count"],
                  "answers_valid_empty": sum(o["status"] == "ok" and not o["claims"] for o in outcomes),
                  "predictions": score["P"]}
        scores = {k: v for k, v in score.items() if k not in ("matches",)}
        if analysis:
            scores["error_analysis"] = analysis
        if store:
            store.finalize_run(run_id, "completed", counts, scores)
    except BaseException as e:           # interrupted / infrastructure failure: run is failed, partial evidence kept
        if store:
            store.finalize_run(run_id, "failed", {"answers_saved": len(outcomes)}, None,
                               {"type": type(e).__name__, "message": str(e)[:300]})
        raise
    lat = [o["latency_ms"] for o in outcomes]
    report = {"run_id": str(run_id), "status": "completed", **{k: v for k, v in meta.items() if k != "created_at"},
              "created_at": meta["created_at"].isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
              "counts": counts, "metrics": scores,
              "timing": {"total_s": round(time.perf_counter() - t_run, 1),
                         "mean_latency_ms": int(sum(lat) / len(lat)) if lat else None, "max_latency_ms": max(lat, default=None)},
              "answers": [{k: o.get(k) for k in ("answer_id", "status", "error", "latency_ms", "turns", "usage", "claims")}
                          for o in outcomes]}
    return report, exchanges
