"""Health check route."""

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from fastapi import Depends

router = APIRouter(tags=["system"])


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
