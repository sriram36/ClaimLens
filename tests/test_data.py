import hashlib
from pathlib import Path

import pytest

from app.data import Catalogue, parse_value, read_csv
from app.errors import UnknownBrand

DATA = Path(__file__).resolve().parent.parent / "data"


def test_csv_quoted_commas_and_embedded_newlines_preserved(tmp_path):
    p = tmp_path / "a.csv"
    raw = 'answer_id,ai_answer\nA01,"Line one, with comma.\n\nSecond  paragraph  with  double spaces. "\n'
    p.write_bytes(raw.encode("utf-8"))
    rows = read_csv(p)
    assert len(rows) == 1                                   # not split by line
    assert rows[0]["ai_answer"] == "Line one, with comma.\n\nSecond  paragraph  with  double spaces. "  # whitespace untouched


def test_real_data_shapes(answers, catalogue, gold):
    assert len(answers) == 50 and sum(a.split == "development" for a in answers) == 40
    assert len(catalogue.facts) == 132 and len(gold) == 376


def test_every_gold_quote_equals_slice_of_unmodified_answer(answers, gold):
    by = {a.answer_id: a.ai_answer for a in answers}
    assert all(by[g.answer_id][g.start_char:g.end_char] == g.quote for g in gold)


def test_boolean_never_uses_python_bool_of_string():
    assert parse_value("false", "boolean") is False and parse_value("true", "boolean") is True
    with pytest.raises(ValueError):
        parse_value("yes", "boolean")
    assert parse_value("1299", "number") == 1299 and parse_value("0.35", "number") == 0.35


def test_blank_unit_and_condition_are_not_applicable(catalogue):
    f = next(f for f in catalogue.facts if f["fact_id"] == "cleartrail.mini.model_name")
    assert f["unit"] is None and f["condition"] is None


def test_catalogue_lookup_tagged_with_fact_version(catalogue):
    r = catalogue.get_brand_facts("cleartrail")
    assert r["fact_version"] == "speaker-catalogue-v4" and len(r["facts"]) == 44
    with pytest.raises(UnknownBrand):
        catalogue.get_brand_facts("acme")


def test_issued_csvs_match_recorded_hashes():
    for line in (DATA / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split()
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest
