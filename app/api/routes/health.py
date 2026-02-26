"""Health check route."""

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from traceback import format_exc

from app.db.session import get_db
from fastapi import Depends

from app.llm.base import LLMRequest, ChatMessage, OutModel
from app.llm.turn_manager_service import TurnManagerService

router = APIRouter(tags=["system"])

buffer = [] # TODO temporary? for test

@router.get("/health")
async def health_check(session=Depends(get_db)):
    """Health check - verifies API and DB connectivity."""
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    }

@router.post("/integrations_test")
async def integrations_test(user_message: str):
    try:
        req = LLMRequest(
            user_message=user_message,
            history=buffer,
            pipeline="default",
        )

        svc = TurnManagerService()
        out = await svc.run(req, payload={"user_profile": {"tone": "friendly"}})
        if out.action == "wait":
            buffer.append(
                ChatMessage(role="user", content=user_message)
            )
        elif out.action == "micro_reply":
            buffer.append(
                ChatMessage(role="user", content=user_message)
            )
            buffer.append(
                ChatMessage(role="assistant", content=out['micro_reply_text'])
            )
        elif out.action  == "respond_safety":
            raise Exception

        elif out.action  == "run_reply_flow":
            buffer.append(
                ChatMessage(role="user", content=user_message)
            )
        elif out.action  == "run_main_flow":
            pass


        return {
            'buffer': [i.to_dict() for i in buffer],
            'out': out,
        }


    except Exception:
        return {
            "user_message": user_message,
            "status": "error",
            "reason": format_exc(),
        }