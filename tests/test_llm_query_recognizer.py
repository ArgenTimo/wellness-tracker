# Tests for QueryRecognizerService and BaseLLMService integration.
# All tests are offline: OpenAI client calls are mocked.

import json
import pytest

from app.llm.base import ChatMessage, LLMRequest
from app.llm.query_recognizer_service import QueryRecognizerService


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _CaptureCreateCall:
    """
    Callable mock that captures arguments passed into chat.completions.create.
    """

    def __init__(self, content: str):
        self.content = content
        self.kwargs = None

    async def __call__(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResponse(self.content)


@pytest.mark.asyncio
async def test_build_messages_includes_system_history_and_user_message(monkeypatch):
    svc = QueryRecognizerService()

    # Override pipelines for deterministic test.
    svc.PIPELINES = {
        "default": type(svc).PIPELINES["default"].__class__(system_prompts=("SYS_1", "SYS_2")),
    }

    req = LLMRequest(
        user_message="Hello",
        history=[
            ChatMessage(role="user", content="Prev user"),
            ChatMessage(role="assistant", content="Prev assistant"),
        ],
        pipeline="default",
    )

    messages = svc.build_messages(req, pipeline=svc.get_pipeline("default"))

    assert messages[0] == {"role": "system", "content": "SYS_1"}
    assert messages[1] == {"role": "system", "content": "SYS_2"}
    assert messages[2] == {"role": "user", "content": "Prev user"}
    assert messages[3] == {"role": "assistant", "content": "Prev assistant"}
    assert messages[4] == {"role": "user", "content": "Hello"}


@pytest.mark.asyncio
async def test_run_passes_json_schema_strict_response_format(monkeypatch):
    svc = QueryRecognizerService()

    # Mock OpenAI create call and capture kwargs.
    output = {
        "queries": [
            {
                "type": "explicit",
                "summary": "Export user's data to JSON.",
                "original_fragment": "export my data to JSON",
            }
        ]
    }
    capture = _CaptureCreateCall(content=json.dumps(output))

    # Patch nested client method: svc.client.chat.completions.create
    # We assume AsyncOpenAI structure exists; override just the create function.
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="export my data to JSON", pipeline="default")
    result = await svc.run(req, payload={})

    assert result.queries[0].type == "explicit"
    assert "Export" in result.queries[0].summary

    # Ensure structured output constraints were passed to the model.
    rf = capture.kwargs["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True

    # The schema should be derived from Pydantic model_json_schema().
    schema = rf["json_schema"]["schema"]
    assert schema["type"] == "object"
    assert "queries" in schema.get("properties", {})


@pytest.mark.asyncio
async def test_run_rejects_extra_fields_in_output(monkeypatch):
    svc = QueryRecognizerService()

    # 'extra_field' is forbidden by ConfigDict(extra="forbid")
    bad_output = {
        "queries": [
            {
                "type": "explicit",
                "summary": "Plot mood vs sleep.",
                "original_fragment": "plot mood vs sleep",
                "extra_field": "NOPE",
            }
        ]
    }
    capture = _CaptureCreateCall(content=json.dumps(bad_output))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="plot mood vs sleep", pipeline="default")

    with pytest.raises(Exception):
        await svc.run(req, payload={})


@pytest.mark.asyncio
async def test_run_fails_on_missing_required_keys(monkeypatch):
    svc = QueryRecognizerService()

    # Missing 'queries' key -> should fail validation.
    capture = _CaptureCreateCall(content=json.dumps({"not_queries": []}))
    svc.client.chat.completions.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="hi", pipeline="default")

    with pytest.raises(Exception):
        await svc.run(req, payload={})


@pytest.mark.asyncio
async def test_request_requires_user_message_or_history():
    # No user_message and empty history should be rejected at request validation.
    with pytest.raises(Exception):
        LLMRequest(user_message=None, history=[], pipeline="default")