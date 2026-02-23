"""Chrono entry and timeline service."""

from datetime import datetime

from app.db.session import DbSession
from app.domain.schemas import ChronoEntryCreate, ChronoEntryResponse
from app.repositories.entry_repository import EntryRepository
from app.repositories.metric_repository import MetricRepository


class EntryService:
    """Handles chrono entries and timeline."""

    def __init__(self, session: DbSession):
        self.entry_repo = EntryRepository(session)
        self.metric_repo = MetricRepository(session)

    async def submit_entry(
        self, user_id: str, data: ChronoEntryCreate, clinic_id: str | None = None
    ) -> ChronoEntryResponse:
        """Submit a new chrono entry."""
        metric = await self.metric_repo.get_by_id(data.metric_id)
        if not metric:
            raise ValueError(f"Metric {data.metric_id} not found")

        entry = await self.entry_repo.create_entry(
            user_id=user_id,
            metric_id=data.metric_id,
            value=str(data.value),
            confidence=data.confidence,
            is_hypothesis=data.is_hypothesis,
            source_message_id=data.source_message_id,
            clinic_id=clinic_id,
        )
        return ChronoEntryResponse.model_validate(entry)

    async def get_timeline(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[ChronoEntryResponse]:
        """Get timeline for a user."""
        entries = await self.entry_repo.get_timeline(
            user_id=user_id,
            limit=limit,
            offset=offset,
            from_date=from_date,
            to_date=to_date,
        )
        return [ChronoEntryResponse.model_validate(e) for e in entries]
