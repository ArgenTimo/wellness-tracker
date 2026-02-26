import pytest

from app.core.config import settings
from app.llm.base import ChatMessage, LLMRequest
from app.llm.turn_manager_service import TurnManagerService


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_turn_manager_real_call_smoke():
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not configured")

    svc = TurnManagerService()

    # Simulate "today messages" (last few)
    history = [
        ChatMessage(role="assistant", content="You can log sleep, mood, or ask for a summary."),
        ChatMessage(role="user", content="Ok."),
    ]

    # User is logging a metric (often should be "wait", but allow "respond" depending on prompt)
    req = LLMRequest(
        history=history,
        user_message="Slept 7 hours. Mood is a bit low.",
        pipeline="default",
        temperature=0.0,
        max_output_tokens=250,
    )

    payload = {
        "user_profile": {
            "tone": "neutral",
            "timezone": "America/Argentina/Salta",
        }
    }

    out = await svc.run(req, payload=payload)

    assert out.action in ("wait", "respond", "respond_safety")
    assert isinstance(out.reason, str) and len(out.reason) > 0
    assert 0.0 <= out.confidence <= 1.0

    # Contract check: if wait -> empty response_text
    if out.action == "wait":
        assert out.response_text == ""
    else:
        assert isinstance(out.response_text, str) and len(out.response_text) > 0