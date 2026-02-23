"""Specialist routes - clients, timeline, summary. Access derived from user_access_links."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentSpecialist, CurrentUser
from app.db.session import DbSession
from app.domain.schemas import ChronoEntryResponse, SummaryResponse, UserResponse
from app.repositories.access_link_repository import AccessLinkRepository
from app.repositories.entry_repository import EntryRepository
from app.repositories.specialist_repository import SpecialistRepository
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/specialist", tags=["specialist"])


@router.get("/clients", response_model=list[UserResponse])
async def get_clients(
    current: CurrentSpecialist,
    session: DbSession,
):
    """Get all clients linked to the current user (from user_access_links). Returns [] if none."""
    specialist_id = current
    repo = SpecialistRepository(session)
    clients = await repo.get_specialist_clients(specialist_id)
    return [UserResponse.model_validate(c) for c in clients]


@router.get("/{client_id}/timeline", response_model=list[ChronoEntryResponse])
async def get_client_timeline(
    client_id: str,
    current: CurrentUser,
    session: DbSession,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):
    """Get timeline for a client. Requires active access link."""
    access_repo = AccessLinkRepository(session)
    if not await access_repo.has_specialist_access(current, client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or access denied",
        )
    entry_repo = EntryRepository(session)
    entries = await entry_repo.get_timeline(
        user_id=client_id,
        limit=limit,
        offset=offset,
        from_date=from_date,
        to_date=to_date,
    )
    return [ChronoEntryResponse.model_validate(e) for e in entries]


@router.get("/{client_id}/summary", response_model=SummaryResponse)
async def get_client_summary(
    client_id: str,
    current: CurrentUser,
    session: DbSession,
    period_days: int = Query(7, ge=1, le=365),
):
    """Get wellness summary for a client. Requires active access link."""
    access_repo = AccessLinkRepository(session)
    if not await access_repo.has_specialist_access(current, client_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or access denied",
        )
    service = AnalyticsService(session)
    return await service.get_summary(user_id=client_id, period_days=period_days)
