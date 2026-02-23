"""Client routes - entries, summary, tasks. Usable without any links."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.db.session import DbSession
from app.domain.schemas import (
    ChronoEntryCreate,
    ChronoEntryResponse,
    SummaryResponse,
    TaskReminderCreate,
    TaskReminderResponse,
)
from app.repositories.task_repository import TaskRepository
from app.services.analytics_service import AnalyticsService
from app.services.entry_service import EntryService

router = APIRouter(prefix="/entries", tags=["client"])
summary_router = APIRouter(prefix="/summary", tags=["client"])
tasks_router = APIRouter(prefix="/tasks", tags=["client"])


@router.post("/submit", response_model=ChronoEntryResponse)
async def submit_entry(
    data: ChronoEntryCreate,
    current: CurrentUser,
    session: DbSession,
):
    """Submit a chrono entry."""
    service = EntryService(session)
    try:
        return await service.submit_entry(current, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/timeline", response_model=list[ChronoEntryResponse])
async def get_timeline(
    current: CurrentUser,
    session: DbSession,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):
    """Get timeline of chrono entries."""
    service = EntryService(session)
    return await service.get_timeline(
        user_id=current,
        limit=limit,
        offset=offset,
        from_date=from_date,
        to_date=to_date,
    )


@summary_router.get("", response_model=SummaryResponse)
async def get_summary(
    current: CurrentUser,
    session: DbSession,
    period_days: int = Query(7, ge=1, le=365),
):
    """Get wellness summary (stub)."""
    service = AnalyticsService(session)
    return await service.get_summary(user_id=current, period_days=period_days)


@tasks_router.post("", response_model=TaskReminderResponse)
async def create_task(
    data: TaskReminderCreate,
    current: CurrentUser,
    session: DbSession,
):
    """Create a task reminder."""
    repo = TaskRepository(session)
    task = await repo.create(
        user_id=current,
        description=data.description,
        due_date=data.due_date,
        auto_generated=data.auto_generated,
    )
    return TaskReminderResponse.model_validate(task)


@tasks_router.get("", response_model=list[TaskReminderResponse])
async def get_tasks(
    current: CurrentUser,
    session: DbSession,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = None,
):
    """Get user's task reminders."""
    repo = TaskRepository(session)
    tasks = await repo.get_by_user(
        user_id=current, limit=limit, offset=offset, status=status
    )
    return [TaskReminderResponse.model_validate(t) for t in tasks]
