import json

import pytest

from app.agent import ClaimsAgent
from app.reports import compare, render_markdown, write_run_artifacts
from app.runner import run_split
from tests.conftest import generic_fake


def _run(v, split, settings, catalogue, answers, gold, fail=()):
    ag = ClaimsAgent(generic_fake(fail_ids=fail), catalogue, v, settings)
    return run_split(agent=ag, answers=answers, split=split, settings=settings, gold=gold)


def test_dev_report_artifacts_and_compare(tmp_path, settings, catalogue, answers, gold):
    r1, ex1 = _run("v1", "development", settings, catalogue, answers, gold)
    r2, _ = _run("v2", "development", settings, catalogue, answers, gold, fail={"A05"})
    paths = write_run_artifacts(r1, ex1, tmp_path, "v1_development")
    md = paths["markdown"].read_text()
    assert "## Missed gold claims" in md and "joint (main)" in md and json.loads(paths["json"].read_text())["run_id"] == r1["run_id"]
    assert len(paths["exchanges"].read_text().splitlines()) == 40
    out = compare(r1, r2, gold)
    assert "Fixed by v2" in out and "Regressions in v2" in out and "answer_error_count" not in out


def test_check_report_states_null_quality(tmp_path, settings, catalogue, answers, gold):
    r, ex = _run("v1", "check", settings, catalogue, answers, gold)
    assert r["metrics"]["quality_available"] is False and r["metrics"]["G"] is None
    assert "null" in render_markdown(r)
    with pytest.raises(ValueError):
        compare(r, r, gold)          # check runs can't be quality-compared
