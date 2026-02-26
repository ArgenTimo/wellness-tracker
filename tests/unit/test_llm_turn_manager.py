# Unit tests for TurnManagerService.
# - MongoDB is mocked via a lightweight repo stub.
# - OpenAI calls are mocked (offline tests).

import json
import pytest

from app.llm.base import ChatMessage, LLMRequest
from app.llm.turn_manager_service import TurnManagerService


# -------------------------
# Fake Mongo repository
# -------------------------

class FakeMongoRepo:
    """
    Minimal async stub that simulates MongoDB storage.
    """

    def __init__(self, profile: dict, today_messages: list[dict]):
        self._profile = profile
        self._today_messages = today_messages

    async def get_user_profile(self, user_id: str) -> dict:
        return self._profile

    async def get_today_messages(self, user_id: str, limit: int = 10) -> list[dict]:
        # Return last N messages (already filtered to "today" by this stub)
        return self._today_messages[-limit:]


def _messages_from_mongo(raw: list[dict]) -> list[ChatMessage]:
    """
    Adapter: convert Mongo JSON messages into normalized ChatMessage objects.
    Expected shape in Mongo (example):
      {"role": "user"|"assistant", "content": "..."}
    """
    return [ChatMessage(role=m["role"], content=m["content"]) for m in raw]


async def _build_turn_manager_call(repo: FakeMongoRepo, user_id: str, latest_user_message: str):
    """
    Demonstrates the "default flow":
    - fetch profile JSON from Mongo
    - fetch today's messages from Mongo
    - build LLMRequest(history=..., user_message=...)
    - call TurnManagerService with payload={"user_profile": profile}
    """
    profile = await repo.get_user_profile(user_id)
    today = await repo.get_today_messages(user_id, limit=10)

    req = LLMRequest(
        history=_messages_from_mongo(today),
        user_message=latest_user_message,
        pipeline="default",
        temperature=0.0,
        max_output_tokens=300,
    )

    svc = TurnManagerService()
    return svc, req, {"user_profile": profile}


# -------------------------
# OpenAI mock helpers
# -------------------------

class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _CaptureChatCreateCall:
    """
    Async callable mock that captures kwargs passed into chat.completions.create.
    """

    def __init__(self, content: str):
        self.content = content
        self.kwargs = None

    async def __call__(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResponse(self.content)


# -------------------------
# Tests
# -------------------------

@pytest.mark.asyncio
async def test_turn_manager_injects_user_profile_into_system_prompt(monkeypatch):
    repo = FakeMongoRepo(
        profile={"tone": "friendly", "timezone": "America/Argentina/Salta"},
        today_messages=[
            {"role": "assistant", "content": "Hi! You can log sleep or mood."},
            {"role": "user", "content": "Ok."},
        ],
    )

    svc, req, payload = await _build_turn_manager_call(repo, "u1", "Slept 7 hours.")

    # Mock OpenAI response (valid strict schema)
    output = {
        "action": "wait",
        "response_text": "",
        "reason": "User is logging a metric without a question.",
        "confidence": 0.85,
    }
    capture = _CaptureChatCreateCall(content=json.dumps(output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    out = await svc.run(req, payload=payload)
    assert out.action == "wait"
    assert out.response_text == ""

    # Assert system prompt contains USER_PROFILE_JSON data
    sent_messages = capture.kwargs["messages"]
    system_msgs = [m for m in sent_messages if m["role"] == "system"]
    assert system_msgs, "Expected a system message"
    sys_text = system_msgs[0]["content"]

    assert "USER_PROFILE_JSON" in sys_text
    assert "America/Argentina/Salta" in sys_text
    assert "friendly" in sys_text


@pytest.mark.asyncio
async def test_turn_manager_uses_last_10_today_messages_plus_latest(monkeypatch):
    # 12 messages "today" -> service should include last 10 + latest_user_message
    today = []
    for i in range(12):
        role = "user" if i % 2 == 0 else "assistant"
        today.append({"role": role, "content": f"m{i}"})

    repo = FakeMongoRepo(profile={}, today_messages=today)
    svc, req, payload = await _build_turn_manager_call(repo, "u1", "Final part")

    output = {
        "action": "respond",
        "response_text": "Got it. Anything else you want to add?",
        "reason": "User likely finished a thought; brief acknowledgement is helpful.",
        "confidence": 0.6,
    }
    capture = _CaptureChatCreateCall(content=json.dumps(output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    await svc.run(req, payload=payload)

    sent_messages = capture.kwargs["messages"]
    non_system = [m for m in sent_messages if m["role"] != "system"]

    # Base history should be last 10 messages + latest user message appended
    # So expected count = 10 (history) + 1 (latest) + possibly earlier assistant in history already included
    # Here we validate the last user message is present and the oldest 2 are not.
    contents = [m["content"] for m in non_system]

    assert "m0" not in contents
    assert "m1" not in contents
    assert "m2" in contents  # depending on cut, m2..m11 are 10 items
    assert "m11" in contents
    assert "Final part" in contents


@pytest.mark.asyncio
async def test_turn_manager_passes_strict_json_schema(monkeypatch):
    repo = FakeMongoRepo(profile={"tone": "neutral"}, today_messages=[])
    svc, req, payload = await _build_turn_manager_call(repo, "u1", "Hello")

    output = {
        "action": "respond",
        "response_text": "Hi — what would you like to do today?",
        "reason": "User greeted; a reply is expected.",
        "confidence": 0.7,
    }
    capture = _CaptureChatCreateCall(content=json.dumps(output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    await svc.run(req, payload=payload)

    rf = capture.kwargs["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True
    schema = rf["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert "action" in schema.get("properties", {})
    assert "response_text" in schema.get("properties", {})
    assert "reason" in schema.get("properties", {})
    assert "confidence" in schema.get("properties", {})


@pytest.mark.asyncio
async def test_turn_manager_rejects_extra_fields(monkeypatch):
    repo = FakeMongoRepo(profile={}, today_messages=[])
    svc, req, payload = await _build_turn_manager_call(repo, "u1", "Hello")

    bad = {
        "action": "respond",
        "response_text": "Hi",
        "reason": "x",
        "confidence": 0.5,
        "extra": "NOPE",
    }
    capture = _CaptureChatCreateCall(content=json.dumps(bad))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    with pytest.raises(Exception):
        await svc.run(req, payload=payload)