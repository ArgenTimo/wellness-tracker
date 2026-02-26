from app.llm.base import LLMRequest
from app.llm.query_recognizer_service import QueryRecognizerService

svc = QueryRecognizerService()

async def test():
    req = LLMRequest(
        user_message="Plot my mood vs sleep for the last 30 days, and set a daily 22:30 reminder.",
        pipeline="default",
    )

    out = await svc.run(req, payload={})
    print(out.model_dump())