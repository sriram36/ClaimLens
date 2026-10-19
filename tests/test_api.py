import pytest
from fastapi.testclient import TestClient

from app import api
from app.providers import ProviderResponse
from app.errors import ProviderFailure, ProviderTimeout
from tests.conftest import final_json, lookup, scripted

BODY = {"answer_id": "A01", "brand_id": "cleartrail", "question": "Q?", "ai_answer": "The Mini has Wi-Fi.", "agent_version": "v1"}


@pytest.fixture
def client(settings):
    api.app.dependency_overrides[api.get_settings] = lambda: settings
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def use(provider):
    api.app.dependency_overrides[api.get_provider_factory] = lambda: (lambda: provider)


def test_classify_200(client):
    use(scripted(lookup(), final_json([{"quote": "The Mini has Wi-Fi.", "label": "unknown", "fact_ids": [], "reason": "No row."}])))
    r = client.post("/classify", json=BODY)
    assert r.status_code == 200 and r.json()["claims"][0]["claim_id"] == "A01:0:19"


@pytest.mark.parametrize("patch", [
    {"agent_version": "v3"}, {"claims": []}, {"expected_label": "supported"}, {"evidence_fact_ids": "x"},
    {"start_char": 0}, {"ai_answer": ""},
])
def test_classify_422_for_invalid_or_gold_fields(client, patch):
    use(scripted())
    assert client.post("/classify", json={**BODY, **patch}).status_code == 422


def test_classify_422_missing_field(client):
    use(scripted())
    b = dict(BODY)
    del b["question"]
    assert client.post("/classify", json=b).status_code == 422


def test_classify_404_unknown_brand(client):
    use(scripted())
    r = client.post("/classify", json={**BODY, "brand_id": "acme"})
    assert r.status_code == 404 and r.json()["error"]["type"] == "unknown_brand"


def test_classify_502_invalid_output_and_provider_failure_and_504_timeout(client):
    use(scripted(lookup(), ProviderResponse([{"type": "text", "text": "garbage"}])))
    r = client.post("/classify", json=BODY)
    assert r.status_code == 502 and r.json()["error"]["type"] == "invalid_output"

    # API keys must never show up in error responses
    use(scripted(ProviderFailure("upstream api_key=SECRETKEYVALUE12345 exploded")))
    r = client.post("/classify", json=BODY)
    assert r.status_code == 502 and "SECRETKEYVALUE12345" not in r.text

    use(scripted(ProviderTimeout("timed out")))
    assert client.post("/classify", json=BODY).status_code == 504


def test_validation_and_unknown_brand_are_not_masked_by_missing_key_or_db(settings, monkeypatch):
    # Validate that 422 and 404 come back correctly even with no credentials configured.
    # The provider is built lazily, so these checks run before we even try to connect.
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    api.app.dependency_overrides[api.get_settings] = lambda: settings
    c = TestClient(api.app)
    try:
        assert c.post("/classify", json={**BODY, "agent_version": "v9"}).status_code == 422
        assert c.post("/classify", json={**BODY, "brand_id": "acme"}).status_code == 404
        assert c.post("/evaluation-runs", json={"agent_version": "v9", "split": "check"}).status_code == 422
        assert c.get("/evaluation-runs/not-a-uuid").status_code == 422
        assert c.post("/classify", json=BODY).status_code == 502          # valid body, missing key -> provider error
        assert c.post("/evaluation-runs", json={"agent_version": "v1", "split": "check"}).status_code in (502, 503)
    finally:
        api.app.dependency_overrides.clear()
