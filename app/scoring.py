"""Deterministic scorer: exact span matching, extraction and joint precision/recall/F1. No LLM judge, no fuzzy matching."""
from __future__ import annotations

from collections import defaultdict

from .data import GoldClaim


def _prf(num: int, p: int, g: int) -> dict:
    return {"precision": num / p if p else 0.0, "recall": num / g if g else 0.0,
            "f1": 2 * num / (p + g) if (p + g) else 0.0}


def validate_outcomes(scheduled_ids: list, outcomes: list) -> None:
    ids = [o["answer_id"] for o in outcomes]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        raise ValueError(f"duplicated answer outcomes: {dups}")
    missing = sorted(set(scheduled_ids) - set(ids))
    extra = sorted(set(ids) - set(scheduled_ids))
    if missing or extra:
        raise ValueError(f"answer outcomes do not match schedule: missing={missing} unexpected={extra}")
    for o in outcomes:
        if o["status"] not in ("ok", "error"):
            raise ValueError(f"bad outcome status for {o['answer_id']}")
        if o["status"] == "error" and o.get("claims"):
            raise ValueError(f"errored answer {o['answer_id']} must have no accepted predictions")


def score_run(split: str, scheduled_ids: list, outcomes: list, gold: list[GoldClaim] | None) -> dict:
    """outcomes: [{"answer_id","status","claims":[claim dicts]}]. For split 'check' (or no gold) quality stays null."""
    validate_outcomes(scheduled_ids, outcomes)
    preds = [(o["answer_id"], c) for o in outcomes if o["status"] == "ok" for c in o["claims"]]
    errors = {o["answer_id"]: (o.get("error") or {}).get("type") for o in outcomes if o["status"] == "error"}
    base = {"P": len(preds), "answer_error_count": len(errors), "answer_errors": errors}
    if split != "development" or not scheduled_ids or gold is None:
        return {**base, "quality_available": False, "G": None, "M": None, "C": None, "extraction": None, "joint": None,
                "coverage": None, "missed_gold_ids": None, "unmatched_prediction_ids": None, "wrong_label_ids": None,
                "per_answer": None, "matches": None}

    gold = [g for g in gold if g.answer_id in set(scheduled_ids)]
    gold_by_span = {(g.answer_id, g.start_char, g.end_char): g for g in gold}
    G = len(gold)
    used, matches = set(), []
    M = C = 0
    unmatched, wrong = [], []
    per = defaultdict(lambda: {"G": 0, "P": 0, "M": 0, "C": 0})
    for g in gold:
        per[g.answer_id]["G"] += 1
    for aid, c in preds:
        per[aid]["P"] += 1
        key = (aid, c["start_char"], c["end_char"])
        g = gold_by_span.get(key)
        if g is None or key in used or c["quote"] != g.quote:      # span identical AND quote equal, one match per gold
            unmatched.append(c["claim_id"])
            matches.append({"answer_id": aid, "start_char": c["start_char"], "end_char": c["end_char"],
                            "matched_gold": False, "expected_label": None, "label_correct": None, "gold_claim_id": None})
            continue
        used.add(key)
        M += 1
        per[aid]["M"] += 1
        ok = c["label"] == g.expected_label
        if ok:
            C += 1
            per[aid]["C"] += 1
        else:
            wrong.append({"claim_id": g.claim_id, "predicted": c["label"], "expected": g.expected_label})
        matches.append({"answer_id": aid, "start_char": c["start_char"], "end_char": c["end_char"], "matched_gold": True,
                        "expected_label": g.expected_label, "label_correct": ok, "gold_claim_id": g.claim_id})
    missed = [g.claim_id for g in gold if (g.answer_id, g.start_char, g.end_char) not in used]
    return {**base, "quality_available": True, "G": G, "M": M, "C": C,
            "extraction": _prf(M, len(preds), G), "joint": _prf(C, len(preds), G), "coverage": C / G if G else 0.0,
            "missed_gold_ids": missed, "unmatched_prediction_ids": unmatched, "wrong_label_ids": wrong,
            "per_answer": dict(per), "matches": matches}


def error_analysis(gold: list[GoldClaim], predictions: dict, score: dict) -> dict:
    """Dev-only records joined AFTER predictions are saved: missed / extra / wrong-label details and per-tag stats."""
    by_id = {g.claim_id: g for g in gold}
    wrong_ids = {w["claim_id"] for w in score["wrong_label_ids"]}
    missed_ids = set(score["missed_gold_ids"])
    tags = defaultdict(lambda: {"G": 0, "correct": 0, "missed": 0, "wrong_label": 0})
    for g in gold:
        for t in g.difficulty_tags:
            tags[t]["G"] += 1
            if g.claim_id in missed_ids:
                tags[t]["missed"] += 1
            elif g.claim_id in wrong_ids:
                tags[t]["wrong_label"] += 1
            else:
                tags[t]["correct"] += 1
    return {
        "missed": [{"claim_id": i, "quote": by_id[i].quote, "expected_label": by_id[i].expected_label,
                    "tags": list(by_id[i].difficulty_tags)} for i in score["missed_gold_ids"]],
        "extra": [{"claim_id": i, "quote": predictions[i]["quote"], "predicted_label": predictions[i]["label"]}
                  for i in score["unmatched_prediction_ids"]],
        "wrong_label": [{**w, "quote": by_id[w["claim_id"]].quote, "explanation": by_id[w["claim_id"]].explanation,
                         "tags": list(by_id[w["claim_id"]].difficulty_tags),
                         "reason": predictions[w["claim_id"]]["reason"]} for w in score["wrong_label_ids"]],
        "by_tag": dict(sorted(tags.items(), key=lambda kv: -kv[1]["G"])),
    }
