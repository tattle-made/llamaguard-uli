import json
from fastapi.testclient import TestClient

from server import app
from service import ModerationReason


client = TestClient(app)


def test_empty_input_returns_400():
    response = client.post("/moderate", json={"text": "  "})
    assert response.status_code == 400
    body = response.json()
    assert body["should_moderate"] is False
    assert body["reason"] is None
    assert body["meta"]["flagged_words"] == []


def test_safe_content_returns_200_safe_reason(monkeypatch):
    # Ensure llama guard returns safe
    from server import moderation_service

    def safe_llama(_):
        return (False, "safe")

    monkeypatch.setattr(moderation_service, "_check_llama_guard", lambda text: safe_llama(text))
    response = client.post("/moderate", json={"text": "hello world"})
    assert response.status_code == 200
    body = response.json()
    assert body["should_moderate"] is False
    assert body["reason"] == ModerationReason.SAFE


def test_slur_list_moderation_returns_200(monkeypatch):
    from server import moderation_service

    # Force slur list to contain a word and hit it
    moderation_service.slur_words = {"badword"}
    response = client.post("/moderate", json={"text": "this has badword in it"})
    assert response.status_code == 200
    body = response.json()
    assert body["should_moderate"] is True
    assert body["reason"] == ModerationReason.SLUR_LIST
    assert "badword" in body["meta"]["flagged_words"]


def test_llama_guard_moderation_returns_200(monkeypatch):
    from server import moderation_service

    def unsafe_llama(_):
        return (True, "unsafe: category")

    monkeypatch.setattr(moderation_service, "_check_llama_guard", lambda text: unsafe_llama(text))
    response = client.post("/moderate", json={"text": "neutral"})
    assert response.status_code == 200
    body = response.json()
    assert body["should_moderate"] is True
    assert body["reason"] == ModerationReason.LLAMA_GUARD


def test_flagged_list_override_returns_safe(monkeypatch):
    from server import moderation_service

    moderation_service.flagged_list_words = {"whitelist"}
    # Force llama guard safe and no slur
    monkeypatch.setattr(moderation_service, "_check_llama_guard", lambda text: (False, "safe"))
    response = client.post("/moderate", json={"text": "contains whitelist term"})
    assert response.status_code == 200
    body = response.json()
    assert body["should_moderate"] is False
    assert body["reason"] == ModerationReason.SAFE
    assert "whitelist" in body["meta"]["flagged_words"]


def test_internal_error_returns_500(monkeypatch):
    from server import moderation_service

    def boom(_):
        raise RuntimeError("boom")

    monkeypatch.setattr(moderation_service, "moderate_content", boom)
    response = client.post("/moderate", json={"text": "anything"})
    assert response.status_code == 500
    body = response.json()
    assert body["status_code"] == 500
    assert body["should_moderate"] is False
