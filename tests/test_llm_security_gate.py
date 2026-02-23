import json
import pytest

from app.llm.base import LLMRequest
from app.llm.security_gate_service import SecurityGateService


class _FakeResponsesResult:
    def __init__(self, output_text: str):
        self.output_text = output_text


class _CaptureResponsesCreate:
    def __init__(self, output_text: str):
        self.output_text = output_text
        self.kwargs = None

    async def __call__(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResponsesResult(self.output_text)


@pytest.mark.asyncio
async def test_security_gate_passes_tools_and_json_schema(monkeypatch):
    svc = SecurityGateService()

    # Force vector store ids for test (avoid dependency on .env)
    from app.core.config import settings
    settings.SECURITY_VECTOR_STORE_IDS[:] = ["vs_test_1"]

    output = {
        "valid_queries": [
            {"type": "explicit", "summary": "Export my data", "original_fragment": "export my data"}
        ],
        "needs_access_check": [],
        "dangerous_queries": [],
    }

    capture = _CaptureResponsesCreate(output_text=json.dumps(output))
    svc.client.responses.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="irrelevant here", pipeline="default")
    result = await svc.run(
        req,
        payload={
            "queries": [
                {"type": "explicit", "summary": "Export my data", "original_fragment": "export my data"}
            ]
        },
    )

    assert len(result.valid_queries) == 1
    assert result.valid_queries[0].summary == "Export my data"

    # Ensure file_search tool is passed with vector_store_ids
    tools = capture.kwargs["tools"]
    assert tools[0]["type"] == "file_search"
    assert tools[0]["vector_store_ids"] == ["vs_test_1"]

    # Ensure strict JSON schema output is requested
    rf = capture.kwargs["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True


@pytest.mark.asyncio
async def test_security_gate_rejects_extra_fields():
    svc = SecurityGateService()
    from app.core.config import settings
    settings.SECURITY_VECTOR_STORE_IDS[:] = ["vs_test_1"]

    bad_output = {
        "valid_queries": [
            {
                "type": "explicit",
                "summary": "ok",
                "original_fragment": "ok",
                "extra": "nope",
            }
        ],
        "needs_access_check": [],
        "dangerous_queries": [],
    }

    capture = _CaptureResponsesCreate(output_text=json.dumps(bad_output))
    svc.client.responses.create = capture  # type: ignore[attr-defined]

    req = LLMRequest(user_message="x", pipeline="default")

    with pytest.raises(Exception):
        await svc.run(req, payload={"queries": [{"type": "explicit", "summary": "ok", "original_fragment": "ok"}]})