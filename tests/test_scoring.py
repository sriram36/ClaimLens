import pytest

from app.data import GoldClaim
from app.scoring import score_run


def G(aid, i, label="supported"):
    s = i * 100
    return GoldClaim(aid, f"{aid}:{s}:{s + 50}", s, s + 50, f"q{aid}{i}", label, (), "x", ("t",))


def P(aid, i, label="supported", quote=None):
    s = i * 100
    return {"claim_id": f"{aid}:{s}:{s + 50}", "start_char": s, "end_char": s + 50, "quote": quote or f"q{aid}{i}",
            "label": label, "fact_ids": [], "reason": "r"}


def ok(aid, claims):
    return {"answer_id": aid, "status": "ok", "claims": claims}


def test_perfect_output():
    gold = [G("A01", 0), G("A01", 1, "unknown")]
    r = score_run("development", ["A01"], [ok("A01", [P("A01", 0), P("A01", 1, "unknown")])], gold)
    assert r["joint"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0} and not r["missed_gold_ids"] and not r["unmatched_prediction_ids"]


def test_spec_example_g10_p10_m8_c7():
    gold = [G("A01", i) for i in range(10)]
    preds = [P("A01", i) for i in range(7)]                       # 7 correct
    preds.append(P("A01", 7, "contradicted"))                      # matched, wrong label  -> M=8, C=7
    preds += [P("A01", 20), P("A01", 21)]                         # 2 extra (no gold)      -> P=10
    r = score_run("development", ["A01"], [ok("A01", preds)], gold)
    assert (r["G"], r["P"], r["M"], r["C"]) == (10, 10, 8, 7)
    assert r["extraction"] == pytest.approx({"precision": 0.8, "recall": 0.8, "f1": 0.8})
    assert r["joint"] == pytest.approx({"precision": 0.7, "recall": 0.7, "f1": 0.7})
    assert r["coverage"] == 0.7 and len(r["wrong_label_ids"]) == 1 and len(r["missed_gold_ids"]) == 2


def test_missed_claim_lowers_recall_and_is_listed():
    gold = [G("A01", 0), G("A01", 1)]
    r = score_run("development", ["A01"], [ok("A01", [P("A01", 0)])], gold)
    assert r["joint"]["recall"] == 0.5 and r["joint"]["precision"] == 1.0 and r["missed_gold_ids"] == ["A01:100:150"]


def test_extra_advice_claim_lowers_precision():
    gold = [G("A01", 0)]
    r = score_run("development", ["A01"], [ok("A01", [P("A01", 0), P("A01", 5)])], gold)
    assert r["joint"]["precision"] == 0.5 and r["unmatched_prediction_ids"] == ["A01:500:550"]


def test_partial_span_is_unmatched():
    gold = [G("A01", 0)]
    partial = P("A01", 0); partial["end_char"] = 40; partial["claim_id"] = "A01:0:40"
    r = score_run("development", ["A01"], [ok("A01", [partial])], gold)
    assert r["M"] == 0 and r["missed_gold_ids"] and r["unmatched_prediction_ids"]


def test_wrong_label_counts_as_match_not_correct():
    r = score_run("development", ["A01"], [ok("A01", [P("A01", 0, "unknown")])], [G("A01", 0)])
    assert (r["M"], r["C"]) == (1, 0) and r["extraction"]["f1"] == 1.0 and r["joint"]["f1"] == 0.0


def test_provider_error_answer_keeps_gold_as_missed_and_adds_no_predictions():
    gold = [G("A01", 0), G("A02", 0)]
    outs = [ok("A01", [P("A01", 0)]),
            {"answer_id": "A02", "status": "error", "claims": [], "error": {"type": "provider_timeout", "message": "x"}}]
    r = score_run("development", ["A01", "A02"], outs, gold)
    assert (r["G"], r["P"], r["C"]) == (2, 1, 1) and r["joint"]["recall"] == 0.5
    assert r["answer_error_count"] == 1 and r["answer_errors"] == {"A02": "provider_timeout"} and r["missed_gold_ids"] == ["A02:0:50"]


def test_valid_empty_predictions_get_zero_not_null():
    r = score_run("development", ["A01"], [ok("A01", [])], [G("A01", 0)])
    assert r["quality_available"] and r["joint"] == {"precision": 0.0, "recall": 0.0, "f1": 0.0} and r["answer_error_count"] == 0


def test_empty_split_has_null_metrics():
    r = score_run("development", [], [], [])
    assert r["quality_available"] is False and r["joint"] is None


def test_missing_and_duplicate_outcomes_rejected():
    with pytest.raises(ValueError):
        score_run("development", ["A01", "A02"], [ok("A01", [])], [G("A01", 0)])
    with pytest.raises(ValueError):
        score_run("development", ["A01"], [ok("A01", []), ok("A01", [])], [G("A01", 0)])
    with pytest.raises(ValueError):
        score_run("development", ["A01"], [ok("A01", []), ok("A09", [])], [G("A01", 0)])


def test_check_split_quality_is_null_but_predictions_counted():
    r = score_run("check", ["A41"], [ok("A41", [P("A41", 0)])], None)
    assert r["P"] == 1 and all(r[k] is None for k in ("G", "M", "C", "extraction", "joint", "coverage", "missed_gold_ids", "wrong_label_ids"))


def test_harness_sanity_on_real_gold_oracle_predictions_score_one(gold):
    """Harness-only check (never an inference path): predictions copied from gold must score 1.0, shifted ones must not."""
    ids = sorted({g.answer_id for g in gold})
    outs = [ok(a, [{"claim_id": g.claim_id, "start_char": g.start_char, "end_char": g.end_char, "quote": g.quote,
                    "label": g.expected_label, "fact_ids": [], "reason": "r"} for g in gold if g.answer_id == a]) for a in ids]
    r = score_run("development", ids, outs, gold)
    assert (r["G"], r["P"], r["M"], r["C"]) == (376, 376, 376, 376) and r["joint"]["f1"] == 1.0
    for o in outs:
        for c in o["claims"]:
            c["end_char"] -= 1                                                   # break every span by one char
    r2 = score_run("development", ids, outs, gold)
    assert r2["M"] == 0 and r2["joint"]["f1"] == 0.0 and len(r2["missed_gold_ids"]) == 376
