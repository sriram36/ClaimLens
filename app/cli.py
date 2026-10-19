"""CLI entry point.

Usage:
    python -m app.cli verify-data
    python -m app.cli run --agent-version v1 --split development [--limit N]
    python -m app.cli compare reports/v1_dev.json reports/v2_dev.json
    python -m app.cli init-db
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent import ClaimsAgent
from .config import Settings
from .data import Catalogue, file_hashes, load_answers, load_gold
from .providers import AzureProvider
from .reports import compare, write_run_artifacts
from .runner import run_split
from .versions import AGENT_VERSIONS, SPLITS


def _load(settings: Settings):
    d = settings.data_dir
    return (
        load_answers(d / "answers.csv"),
        Catalogue.load(d / "brand_facts.csv"),
        load_gold(d / "development_gold.csv"),
    )


def cmd_verify(settings, args):
    answers, cat, gold = _load(settings)
    by = {a.answer_id: a.ai_answer for a in answers}
    bad = [g.claim_id for g in gold if by[g.answer_id][g.start_char:g.end_char] != g.quote]
    print(
        f"answers={len(answers)} facts={len(cat.facts)} gold={len(gold)} "
        f"brands={cat.brand_ids} gold_slice_mismatches={len(bad)}"
    )
    print(json.dumps(file_hashes(settings.data_dir), indent=2))
    return 1 if bad else 0


def cmd_run(settings, args):
    answers, cat, gold = _load(settings)
    provider = AzureProvider(
        deployment=settings.deployment,
        api_version=settings.api_version,
        max_retries=settings.max_retries,
        temperature=settings.temperature,
    )
    agent = ClaimsAgent(provider, cat, args.agent_version, settings)

    store = None
    if args.save_db:
        from .db import Store
        store = Store()
        store.init_schema()

    label = args.label or f"{args.agent_version}_{args.split}"

    def progress(n, total, o):
        err = (o["error"] or {}).get("type", "")
        print(
            f"[{n}/{total}] {o['answer_id']}  {o['status']}  "
            f"claims={len(o['claims'])}  {o['latency_ms']}ms  {err}",
            flush=True,
        )

    report, exchanges = run_split(
        agent=agent,
        answers=answers,
        split=args.split,
        settings=settings,
        gold=gold,
        store=store,
        progress=progress,
        limit=args.limit,
    )
    paths = write_run_artifacts(report, exchanges, Path(args.out), label)
    m = report["metrics"]

    print(f"\nrun {report['run_id']} -> {paths['markdown']}")
    if m["quality_available"]:
        print(
            f"joint F1={m['joint']['f1']:.3f}  "
            f"extraction F1={m['extraction']['f1']:.3f}  "
            f"G={m['G']} P={m['P']} M={m['M']} C={m['C']}  "
            f"errors={m['answer_error_count']}"
        )
    else:
        print(f"check run: predictions saved, quality null. P={m['P']} errors={m['answer_error_count']}")
    return 0


def cmd_compare(settings, args):
    gold = load_gold(settings.data_dir / "development_gold.csv")
    v1 = json.loads(Path(args.v1).read_text(encoding="utf-8"))
    v2 = json.loads(Path(args.v2).read_text(encoding="utf-8"))
    md = compare(v1, v2, gold)
    Path(args.out).write_text(md, encoding="utf-8")
    print(md)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="app.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db")
    sub.add_parser("verify-data")

    r = sub.add_parser("run")
    r.add_argument("--agent-version", choices=AGENT_VERSIONS, required=True)
    r.add_argument("--split", choices=SPLITS, required=True)
    r.add_argument("--limit", type=int, help="first N answers only (smoke-test; not valid evidence)")
    r.add_argument("--out", default="reports")
    r.add_argument("--label")
    r.add_argument("--save-db", action="store_true")

    c = sub.add_parser("compare")
    c.add_argument("v1")
    c.add_argument("v2")
    c.add_argument("--out", default="reports/comparison_v1_v2_development.md")

    args = p.parse_args(argv)
    settings = Settings.from_env()

    if args.cmd == "init-db":
        from .db import Store
        Store().init_schema()
        print("schema ready")
        return 0

    dispatch = {"verify-data": cmd_verify, "run": cmd_run, "compare": cmd_compare}
    return dispatch[args.cmd](settings, args)


if __name__ == "__main__":
    sys.exit(main())
