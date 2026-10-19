"""Strict output validation: spans, quote equality, IDs, labels, fact IDs, ordering, overlaps."""
from __future__ import annotations

import re

from .errors import InvalidOutput
from .versions import LABELS

CLAIM_KEYS = {"claim_id", "start_char", "end_char", "quote", "label", "fact_ids", "reason"}
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def split_sentences(text: str) -> list[str]:
    return [s for s in _SENT_SPLIT.split(text.strip()) if s]


def limit_two_sentences(reason: str) -> str:
    return " ".join(split_sentences(reason)[:2])


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate_claims(answer_id: str, ai_answer: str, claims: list, known_fact_ids: set) -> list[dict]:
    """Return claims unchanged if valid; raise InvalidOutput otherwise."""
    if not isinstance(claims, list):
        raise InvalidOutput("claims must be a list")
    seen_ids: set = set()
    prev_end = 0
    prev_start = -1
    for i, c in enumerate(claims):
        where = f"claim[{i}]"
        if not isinstance(c, dict) or set(c) != CLAIM_KEYS:
            raise InvalidOutput(f"{where}: wrong keys")
        s, e, q = c["start_char"], c["end_char"], c["quote"]
        if not (_is_int(s) and _is_int(e)):
            raise InvalidOutput(f"{where}: offsets must be integers")
        if not (0 <= s < e <= len(ai_answer)):
            raise InvalidOutput(f"{where}: span out of bounds")
        if not isinstance(q, str) or q != ai_answer[s:e]:
            raise InvalidOutput(f"{where}: quote does not equal ai_answer[start:end]")
        if q != q.strip():
            raise InvalidOutput(f"{where}: quote has leading/trailing whitespace")
        if c["claim_id"] != f"{answer_id}:{s}:{e}":
            raise InvalidOutput(f"{where}: claim_id is not answer_id:start:end")
        if c["claim_id"] in seen_ids:
            raise InvalidOutput(f"{where}: duplicate claim_id")
        seen_ids.add(c["claim_id"])
        if s <= prev_start:
            raise InvalidOutput(f"{where}: not in increasing start_char order")
        if s < prev_end:
            raise InvalidOutput(f"{where}: overlaps previous claim")
        prev_start, prev_end = s, e
        if c["label"] not in LABELS:
            raise InvalidOutput(f"{where}: unsupported label")
        fids = c["fact_ids"]
        if not isinstance(fids, list) or not all(isinstance(x, str) for x in fids):
            raise InvalidOutput(f"{where}: fact_ids must be a list of strings")
        if len(set(fids)) != len(fids):
            raise InvalidOutput(f"{where}: duplicate fact_ids")
        bad = [x for x in fids if x not in known_fact_ids]
        if bad:
            raise InvalidOutput(f"{where}: unknown fact_ids {bad[:3]}")
        r = c["reason"]
        if not isinstance(r, str) or len(split_sentences(r)) > 2:
            raise InvalidOutput(f"{where}: reason must be a string of at most two sentences")
    return claims
