import json
import os
from pathlib import Path

import pytest

from app.config import Settings
from app.data import Catalogue, load_answers, load_gold
from app.providers import FakeProvider, ProviderResponse, text, tool_use
from app.validate import split_sentences

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="session")
def settings():
    return Settings(provider_timeout_s=5.0)


@pytest.fixture(scope="session")
def catalogue():
    return Catalogue.load(DATA / "brand_facts.csv")


@pytest.fixture(scope="session")
def answers():
    return load_answers(DATA / "answers.csv")


@pytest.fixture(scope="session")
def gold():
    return load_gold(DATA / "development_gold.csv")


def final_json(claims):
    return ProviderResponse([text(json.dumps({"claims": claims}))], "end_turn", {"input_tokens": 10, "output_tokens": 5})


def lookup(brand="cleartrail", tid="tu_1"):
    return ProviderResponse([tool_use("get_brand_facts", {"brand_id": brand}, tid)], "tool_use", {"input_tokens": 10, "output_tokens": 5})


def scripted(*steps):
    return FakeProvider(list(steps))


def generic_fake(fail_ids=()):
    """Gold-free fake model for whole-split tests: looks up the primary brand, then 'extracts' the first sentence."""
    from app.errors import ProviderTimeout

    def script(kw):
        msgs = kw["messages"]
        first = msgs[0]["content"]
        aid = first.split("answer_id: ")[1].split("\n")[0]
        if aid in fail_ids:
            return ProviderTimeout("provider request timed out after 5s")
        if len(msgs) == 1:
            brand = first.split("primary brand_id: ")[1].split("\n")[0]
            return lookup(brand)
        ans = first.split("<ai_answer>\n")[1].rsplit("\n</ai_answer>", 1)[0]
        sent = split_sentences(ans)[0]
        return final_json([{"quote": sent, "label": "unknown", "fact_ids": [], "reason": "Not covered by catalogue."}])
    return FakeProvider(script)
