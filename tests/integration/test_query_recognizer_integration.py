"""
Real integration test for QueryRecognizerService.

Requires:
- Valid OPENAI_API_KEY in environment
- Internet connection

Run explicitly with:
pytest -m integration
"""

import pytest

from app.core.config import settings
from app.llm.base import LLMRequest
from app.llm.query_recognizer_service import QueryRecognizerService


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_query_recognizer_real_call():
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not configured")

    svc = QueryRecognizerService()

    req = LLMRequest(
        user_message=(
            "Plot my mood vs sleep for the last 30 days "
            "and set a daily 22:30 reminder to log anxiety."
        ),
        pipeline="default",
        temperature=0.0,
    )

    result = await svc.run(req, payload={})

    # Basic structural assertions
    assert isinstance(result.queries, list)
    assert len(result.queries) >= 1

    for q in result.queries:
        assert q.type in ("explicit", "implicit")
        assert isinstance(q.summary, str)
        assert isinstance(q.original_fragment, str)