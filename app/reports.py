"""Local reports: JSON + Markdown per run, JSONL of sanitized model/tool exchanges, v1-vs-v2 comparison."""
from __future__ import annotations

import json
from pathlib import Path

from .errors import sanitize


def _pct(x):
    return "null" if x is None else f"{x:.3f}"


def sanitize_exchanges(exchanges: list) -> list:
    """Redact anything key-shaped from stored text blocks (defence in depth; keys are never in payloads)."""
    def walk(o):
        if isinstance(o, str):
            return sanitize(o, limit=10**7) if ("sk-" in o or "api_key" in o.lower()) else o
        if isinstance(o, list):
            return [walk(x) for x in o]
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        return o
    return walk(exchanges)


def write_run_artifacts(report: dict, exchanges: list, out_dir: Path, label: str) -> dict:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    jp, mp, xp = out_dir / f"{label}.json", out_dir / f"{label}.md", out_dir / f"{label}.exchanges.jsonl"
    jp.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    mp.write_text(render_markdown(report), encoding="utf-8")
    with open(xp, "w", encoding="utf-8") as fh:
        for ex in sanitize_exchanges(exchanges):
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")
    return {"json": jp, "markdown": mp, "exchanges": xp}


def render_markdown(r: dict) -> str:
    m, c = r["metrics"], r["counts"]
    L = [f"# Run {r['run_id']}", "",
         f"- split: **{r['split']}**  |  agent: **{r['agent_version']}** ({r['prompt_version']})  |  status: {r['status']}",
         f"- provider/model: {r['provider']} / {r['model']}",
         f"- versions: dataset `{r['dataset_version']}`, facts `{r['fact_version']}`, evaluator `{r['evaluator_version']}`",
         f"- settings: `{json.dumps(r['settings'])}`", f"- source revision: {r.get('source_revision')}",
         f"- created: {r['created_at']}  |  total {r['timing']['total_s']}s, mean answer latency {r['timing']['mean_latency_ms']} ms",
         f"- file hashes: " + ", ".join(f"{k}={v[:12]}" for k, v in r["file_hashes"].items()), "",
         "## Counts", "", f"scheduled {c['answers_scheduled']} | ok {c['answers_ok']} | errors {c['answers_error']} | "
         f"valid-empty {c['answers_valid_empty']} | accepted predictions P={c['predictions']}", ""]
    if m["answer_errors"]:
        L += ["Answer errors: " + ", ".join(f"{k} ({v})" for k, v in m["answer_errors"].items()), ""]
    L += ["## Metrics", ""]
    if not m["quality_available"]:
        L += ["Quality metrics are **null** for check runs (no ground truth available to the submitter); "
              "G, M, C, matched IDs and correctness are null. Reviewer scores the saved predictions with the private key.", ""]
    else:
        L += ["| | precision | recall | F1 |", "|---|---|---|---|",
              f"| extraction | {_pct(m['extraction']['precision'])} | {_pct(m['extraction']['recall'])} | {_pct(m['extraction']['f1'])} |",
              f"| **joint (main)** | {_pct(m['joint']['precision'])} | {_pct(m['joint']['recall'])} | **{_pct(m['joint']['f1'])}** |", "",
              f"G={m['G']} P={m['P']} M={m['M']} C={m['C']}  |  coverage C/G = {_pct(m['coverage'])}", ""]
        ea = m["error_analysis"]
        L += [f"## Missed gold claims ({len(ea['missed'])})", ""]
        L += [f"- `{x['claim_id']}` [{x['expected_label']}; {','.join(x['tags'])}] {x['quote']}" for x in ea["missed"]] or ["- none"]
        L += ["", f"## Unmatched predictions / extra claims ({len(ea['extra'])})", ""]
        L += [f"- `{x['claim_id']}` [{x['predicted_label']}] {x['quote']}" for x in ea["extra"]] or ["- none"]
        L += ["", f"## Matched but wrong label ({len(ea['wrong_label'])})", ""]
        L += [f"- `{x['claim_id']}` predicted **{x['predicted']}**, expected **{x['expected']}** [{','.join(x['tags'])}]\n"
              f"  - quote: {x['quote']}\n  - gold: {x['explanation']}\n  - model: {x['reason']}" for x in ea["wrong_label"]] or ["- none"]
        L += ["", "## By difficulty tag (G / correct / missed / wrong-label)", "", "| tag | G | correct | missed | wrong |", "|---|---|---|---|---|"]
        L += [f"| {t} | {s['G']} | {s['correct']} | {s['missed']} | {s['wrong_label']} |" for t, s in ea["by_tag"].items()]
    L += ["", "## Per-answer outcomes", "", "| answer | status | claims | latency ms | error |", "|---|---|---|---|---|"]
    L += [f"| {a['answer_id']} | {a['status']} | {len(a['claims'])} | {a['latency_ms']} | {(a['error'] or {}).get('type', '')} |"
          for a in r["answers"]]
    return "\n".join(L) + "\n"


def compare(v1: dict, v2: dict, gold: list) -> str:
    """Fair-comparison report on identical development inputs: metrics delta plus per-claim fixes and regressions."""
    for k in ("split", "dataset_version", "evaluator_version", "fact_version", "provider", "model"):
        if v1[k] != v2[k]:
            raise ValueError(f"runs are not comparable: {k} differs ({v1[k]!r} vs {v2[k]!r})")
    if v1["file_hashes"] != v2["file_hashes"]:
        raise ValueError("runs are not comparable: input file hashes differ")
    if v1["split"] != "development":
        raise ValueError("quality comparison needs development runs")
    gold_ids = {g.claim_id: g for g in gold}

    def status(rep):
        e = rep["metrics"]["error_analysis"]
        miss = {x["claim_id"] for x in e["missed"]}
        wrong = {x["claim_id"]: x for x in e["wrong_label"]}
        return {i: ("missed" if i in miss else "wrong_label" if i in wrong else "correct") for i in gold_ids}

    s1, s2 = status(v1), status(v2)
    fixed = [i for i in gold_ids if s1[i] != "correct" and s2[i] == "correct"]
    regressed = [i for i in gold_ids if s1[i] == "correct" and s2[i] != "correct"]
    m1, m2 = v1["metrics"], v2["metrics"]
    row = lambda name, a, b: f"| {name} | {_pct(a)} | {_pct(b)} | {b - a:+.3f} |"
    L = ["# v1 vs v2 (development, identical inputs and scoring)", "",
         f"- v1 run `{v1['run_id']}` ({v1['prompt_version']}), v2 run `{v2['run_id']}` ({v2['prompt_version']})",
         f"- provider/model: {v1['provider']} / {v1['model']}; settings v1 `{json.dumps(v1['settings'])}` v2 `{json.dumps(v2['settings'])}`", "",
         "| metric | v1 | v2 | delta |", "|---|---|---|---|",
         row("joint F1 (main)", m1["joint"]["f1"], m2["joint"]["f1"]),
         row("joint precision", m1["joint"]["precision"], m2["joint"]["precision"]),
         row("joint recall", m1["joint"]["recall"], m2["joint"]["recall"]),
         row("extraction F1", m1["extraction"]["f1"], m2["extraction"]["f1"]),
         row("coverage C/G", m1["coverage"], m2["coverage"]), "",
         f"Counts v1: G={m1['G']} P={m1['P']} M={m1['M']} C={m1['C']} errors={m1['answer_error_count']}",
         f"Counts v2: G={m2['G']} P={m2['P']} M={m2['M']} C={m2['C']} errors={m2['answer_error_count']}", "",
         f"## Fixed by v2 ({len(fixed)})", ""]
    L += [f"- `{i}` {s1[i]} -> correct: {gold_ids[i].quote[:140]}" for i in fixed] or ["- none"]
    L += ["", f"## Regressions in v2 ({len(regressed)})", ""]
    L += [f"- `{i}` correct -> {s2[i]}: {gold_ids[i].quote[:140]}" for i in regressed] or ["- none"]
    L += ["", f"Net claims correct: v1 {m1['C']} -> v2 {m2['C']} ({m2['C'] - m1['C']:+d}). "
          "A zero or negative delta is a valid measured result; state it as such in the write-up."]
    return "\n".join(L) + "\n"
