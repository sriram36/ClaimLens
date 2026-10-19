import pytest

from app.errors import InvalidOutput
from app.validate import limit_two_sentences, validate_claims

TEXT = "Alpha is cheap. Beta is not.  Gamma costs 5."
IDS = {"f.1", "f.2"}


def claim(s, e, **kw):
    c = {"claim_id": f"A01:{s}:{e}", "start_char": s, "end_char": e, "quote": TEXT[s:e], "label": "unknown",
         "fact_ids": [], "reason": "Fine."}
    c.update(kw)
    return c


def v(claims):
    return validate_claims("A01", TEXT, claims, IDS)


def test_valid_and_empty():
    assert v([claim(0, 15), claim(16, 27)]) and v([]) == []


@pytest.mark.parametrize("bad", [
    claim(0, 999), claim(-1, 5), claim(5, 5), claim(0, 15, quote="Alpha is cheap"),
    claim(0, 16, quote="Alpha is cheap. "),                       # trailing whitespace
    claim(0, 15, claim_id="A01:0:14"), claim(0, 15, label="maybe"), claim(0, 15, fact_ids=["nope"]),
    claim(0, 15, fact_ids=["f.1", "f.1"]), claim(0, 15, reason="One. Two. Three."),
    claim(0, 15, start_char=True),
])
def test_invalid_single_claims_rejected(bad):
    with pytest.raises(InvalidOutput):
        v([bad])


def test_duplicate_ids_overlap_and_order():
    with pytest.raises(InvalidOutput):
        v([claim(0, 15), claim(0, 15)])
    with pytest.raises(InvalidOutput):
        v([claim(0, 15), claim(10, 27)])          # overlap
    with pytest.raises(InvalidOutput):
        v([claim(16, 27), claim(0, 15)])          # not increasing


def test_extra_or_missing_keys_rejected():
    c = claim(0, 15); c["extra"] = 1
    with pytest.raises(InvalidOutput):
        v([c])


def test_reason_limited_to_two_sentences():
    assert limit_two_sentences("A fact. Another fact. Third one.") == "A fact. Another fact."
    assert limit_two_sentences("Costs 0.35 kg vs. 1100 g here.") == "Costs 0.35 kg vs. 1100 g here."
