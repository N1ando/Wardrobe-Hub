"""Gemma client request shape: pinned against the live vLLM deploy.

Gemma-2's chat template rejects the "system" role — vLLM returns HTTP 400 and
the ladder silently falls back to keyword mining, which is exactly what
happened on the demo box. These tests pin the payload shape so the bug can't
come back.
"""

from __future__ import annotations


class _FakeResponse:
    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"choices": [{"message": {"content": " ok "}}]}


def test_chat_payload_never_uses_system_role(monkeypatch):
    from app.ai import gemma_client

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        return _FakeResponse()

    monkeypatch.setattr(gemma_client.httpx, "post", fake_post)
    text = gemma_client._chat("http://box:30000/v1", "", "fitos-gemma", "SYS PROMPT", "USER TEXT", 0.2)

    assert text == "ok"
    assert captured["url"] == "http://box:30000/v1/chat/completions"
    messages = captured["payload"]["messages"]
    assert [m["role"] for m in messages] == ["user"]
    # The system prompt still reaches the model, folded into the user turn.
    assert messages[0]["content"].startswith("SYS PROMPT")
    assert "USER TEXT" in messages[0]["content"]


def test_chat_payload_without_system_prompt_is_plain_user(monkeypatch):
    from app.ai import gemma_client

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["payload"] = json
        return _FakeResponse()

    monkeypatch.setattr(gemma_client.httpx, "post", fake_post)
    gemma_client._chat("http://box:30000/v1", "", "fitos-gemma", "", "USER ONLY", 0.2)

    messages = captured["payload"]["messages"]
    assert [m["role"] for m in messages] == ["user"]
    assert messages[0]["content"] == "USER ONLY"
