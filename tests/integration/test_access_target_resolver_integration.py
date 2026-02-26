import pytest

from app.core.config import settings
from app.llm.base import LLMRequest
from app.llm.access_target_resolver_service import AccessTargetResolverService


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_access_target_resolver_real_call_smoke():
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not configured")

    svc = AccessTargetResolverService()

    available_users = {
        "123": {"id": "123", "name": "Nick Abbott"},
        "777": {"id": "777", "name": "Alice Johnson"},
    }

    payload = {
        "needs_access_check": [
            {
                "type": "explicit",
                "summary": "Show Nick Abbott's anxiety spikes last week.",
                "original_fragment": "show Nick Abbott's anxiety spikes last week",
            },
            {
                "type": "explicit",
                "summary": "Export Alice Johnson timeline to CSV.",
                "original_fragment": "export Alice Johnson timeline to CSV",
            },
        ],
        "available_users": available_users,
    }

    req = LLMRequest(
        user_message="resolve access targets",
        pipeline="default",
        temperature=0.0,
        max_output_tokens=900,
    )

    out = await svc.run(req, payload=payload)

    # Structural invariants
    assert isinstance(out.resolved, list)
    assert isinstance(out.unresolved, list)

    # Must not lose items: every input query text should be either resolved or unresolved
    input_texts = {q["original_fragment"] for q in payload["needs_access_check"]}
    output_texts = {x.text for x in out.resolved} | {x.text for x in out.unresolved}
    assert input_texts == output_texts

    # At least one should resolve deterministically (Nick / Alice are exact names)
    assert len(out.resolved) >= 1
    for r in out.resolved:
        assert r.target_user_id in available_users
        assert r.target_user_name == available_users[r.target_user_id]["name"]
        assert r.match_type in ("id", "name_token")