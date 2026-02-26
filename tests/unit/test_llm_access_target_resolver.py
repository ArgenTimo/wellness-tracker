# Unit tests for AccessTargetResolverService (offline, OpenAI is mocked).

import json
import pytest

from app.llm.base import ChatMessage, LLMRequest
from app.llm.access_target_resolver_service import AccessTargetResolverService


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


@pytest.mark.asyncio
async def test_access_target_resolver_injects_available_users_into_system_prompt(monkeypatch):
    svc = AccessTargetResolverService()

    # Mock OpenAI response (valid strict schema)
    output = {
        "resolved": [
            {
                "text": "show his anxiety spikes last week",
                "target_user_id": "123",
                "target_user_name": "Nick Abbott",
                "match_type": "name_token",
            }
        ],
        "unresolved": [],
    }
    capture = _CaptureChatCreateCall(content=json.dumps(output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(
        user_message="irrelevant",
        history=[ChatMessage(role="assistant", content="ok")],
        pipeline="default",
        temperature=0.0,
        max_output_tokens=800,
    )

    payload = {
        "needs_access_check": [
            {
                "type": "explicit",
                "summary": "Show Nick Abbott's anxiety spikes last week.",
                "original_fragment": "show his anxiety spikes last week",
            }
        ],
        "available_users": {
            "123": {"id": "123", "name": "Nick Abbott"},
        },
    }

    result = await svc.run(req, payload=payload)
    assert result.resolved[0].target_user_id == "123"

    # Validate system prompt includes available users list
    sent_messages = capture.kwargs["messages"]
    system_msgs = [m for m in sent_messages if m["role"] == "system"]
    assert system_msgs, "Expected at least one system message"
    sys_text = system_msgs[0]["content"]

    assert "AVAILABLE_USERS" in sys_text
    assert "Nick Abbott" in sys_text
    assert "123" in sys_text


@pytest.mark.asyncio
async def test_access_target_resolver_user_payload_contains_only_needs_access_check(monkeypatch):
    svc = AccessTargetResolverService()

    output = {"resolved": [], "unresolved": []}
    capture = _CaptureChatCreateCall(content=json.dumps(output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="x", pipeline="default", temperature=0.0)

    payload = {
        "needs_access_check": [
            {
                "type": "explicit",
                "summary": "Export Nick Abbott's timeline to CSV.",
                "original_fragment": "export his timeline to CSV",
            }
        ],
        "available_users": {
            "123": {"id": "123", "name": "Nick Abbott"},
            "777": {"id": "777", "name": "Alice Johnson"},
        },
    }

    await svc.run(req, payload=payload)

    sent_messages = capture.kwargs["messages"]
    user_msgs = [m for m in sent_messages if m["role"] == "user"]
    assert user_msgs, "Expected at least one user message"

    # We append an extra user message containing needs_access_check JSON payload
    last_user = user_msgs[-1]["content"]
    data = json.loads(last_user)

    assert "needs_access_check" in data
    assert len(data["needs_access_check"]) == 1

    # Crucial: available_users must NOT be sent in user payload (it's injected into system prompt)
    assert "available_users" not in data


@pytest.mark.asyncio
async def test_access_target_resolver_passes_strict_json_schema(monkeypatch):
    svc = AccessTargetResolverService()

    output = {"resolved": [], "unresolved": []}
    capture = _CaptureChatCreateCall(content=json.dumps(output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="x", pipeline="default")

    payload = {
        "needs_access_check": [],
        "available_users": {"123": {"id": "123", "name": "Nick Abbott"}},
    }

    await svc.run(req, payload=payload)

    rf = capture.kwargs["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True
    schema = rf["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert "resolved" in schema.get("properties", {})
    assert "unresolved" in schema.get("properties", {})


@pytest.mark.asyncio
async def test_access_target_resolver_rejects_extra_fields_in_output(monkeypatch):
    svc = AccessTargetResolverService()

    # Extra key in resolved item -> should fail Pydantic validation (extra="forbid")
    bad_output = {
        "resolved": [
            {
                "text": "show his anxiety spikes last week",
                "target_user_id": "123",
                "target_user_name": "Nick Abbott",
                "match_type": "name_token",
                "extra": "NOPE",
            }
        ],
        "unresolved": [],
    }
    capture = _CaptureChatCreateCall(content=json.dumps(bad_output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="x", pipeline="default")

    payload = {
        "needs_access_check": [
            {
                "type": "explicit",
                "summary": "Show Nick Abbott's anxiety spikes last week.",
                "original_fragment": "show his anxiety spikes last week",
            }
        ],
        "available_users": {"123": {"id": "123", "name": "Nick Abbott"}},
    }

    with pytest.raises(Exception):
        await svc.run(req, payload=payload)


@pytest.mark.asyncio
async def test_access_target_resolver_requires_message_or_history():
    # Standard LLMRequest invariant test (shared behavior)
    with pytest.raises(Exception):
        LLMRequest(user_message=None, history=[], pipeline="default")