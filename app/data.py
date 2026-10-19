"""CSV loading (csv module, UTF-8, newline='' so quoted commas/line breaks are data) and the fact catalogue."""
from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import UnknownBrand
from .versions import FACT_VERSION

DATA_FILES = ("answers.csv", "brand_facts.csv", "development_gold.csv")


def read_csv(path: Path) -> list[dict]:
    # newline='' is essential: embedded line breaks must reach us untouched.
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@dataclass(frozen=True)
class Answer:
    answer_id: str
    split: str
    brand_id: str
    question: str
    ai_answer: str


@dataclass(frozen=True)
class AgentInput:
    """The ONLY thing the model path ever sees. No gold, labels, spans or claim lists."""
    answer_id: str
    brand_id: str
    question: str
    ai_answer: str

    @classmethod
    def from_answer(cls, a: Answer) -> "AgentInput":
        return cls(a.answer_id, a.brand_id, a.question, a.ai_answer)


@dataclass(frozen=True)
class GoldClaim:
    answer_id: str
    claim_id: str
    start_char: int
    end_char: int
    quote: str
    expected_label: str
    evidence_fact_ids: tuple
    explanation: str
    difficulty_tags: tuple


def load_answers(path: Path) -> list[Answer]:
    return [Answer(r["answer_id"], r["split"], r["brand_id"], r["question"], r["ai_answer"]) for r in read_csv(path)]


def load_gold(path: Path) -> list[GoldClaim]:
    out = []
    for r in read_csv(path):
        out.append(GoldClaim(
            r["answer_id"], r["claim_id"], int(r["start_char"]), int(r["end_char"]), r["quote"],
            r["expected_label"],
            tuple(x for x in r["evidence_fact_ids"].split("|") if x),
            r["explanation"],
            tuple(x for x in r["difficulty_tags"].split("|") if x),
        ))
    return out


def parse_value(value: str, value_type: str):
    """number -> int/float, boolean -> real bool ("false" is False), string -> str."""
    if value_type == "number":
        return int(value) if re.fullmatch(r"-?\d+", value.strip()) else float(value)
    if value_type == "boolean":
        v = value.strip().lower()
        if v not in ("true", "false"):
            raise ValueError(f"bad boolean text: {value!r}")
        return v == "true"
    if value_type == "string":
        return value
    raise ValueError(f"unknown value_type: {value_type!r}")


def _none_if_blank(v: str):
    return v if v.strip() else None  # blank unit/condition means "not applicable"


class Catalogue:
    def __init__(self, rows: list[dict]):
        self.facts: list[dict] = []
        for r in rows:
            self.facts.append({
                "fact_id": r["fact_id"], "brand_id": r["brand_id"], "model_id": r["model_id"],
                "field": r["field"], "value": parse_value(r["value"], r["value_type"]),
                "value_type": r["value_type"], "unit": _none_if_blank(r["unit"]),
                "condition": _none_if_blank(r["condition"]),
                "valid_from": r["valid_from"], "valid_to": r["valid_to"],
            })
        self.fact_ids = {f["fact_id"] for f in self.facts}
        self.brand_ids = sorted({f["brand_id"] for f in self.facts})

    @classmethod
    def load(cls, path: Path) -> "Catalogue":
        return cls(read_csv(path))

    def has_brand(self, brand_id: str) -> bool:
        return brand_id in self.brand_ids

    def get_brand_facts(self, brand_id: str) -> dict:
        """Read-only lookup: all fact rows of a brand, tagged with the fact version."""
        if not isinstance(brand_id, str) or brand_id not in self.brand_ids:
            raise UnknownBrand(f"unknown brand_id: {str(brand_id)[:60]!r}")
        return {"fact_version": FACT_VERSION, "brand_id": brand_id,
                "facts": [dict(f) for f in self.facts if f["brand_id"] == brand_id]}


def file_hashes(data_dir: Path) -> dict:
    return {n: hashlib.sha256((Path(data_dir) / n).read_bytes()).hexdigest() for n in DATA_FILES}
