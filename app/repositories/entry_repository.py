"""Chrono entry and related repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ChronoEntry, Evidence


class EntryRepository:
    """Repository for chrono entries and evidence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_entry(
        self,
        user_id: str,
        metric_id: str,
        value: str,
        confidence: float = 1.0,
        is_hypothesis: bool = False,
        source_message_id: str | None = None,
        clinic_id: str | None = None,
    ) -> ChronoEntry:
        """Create a chrono entry."""
        entry = ChronoEntry(
            user_id=user_id,
            metric_id=metric_id,
            value=value,
            confidence=confidence,
            is_hypothesis=is_hypothesis,
            source_message_id=source_message_id,
            clinic_id=clinic_id,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_timeline(
        self,
        user_id: str | UUID,
        limit: int = 100,
        offset: int = 0,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[ChronoEntry]:
        """Get chrono entries for a user, ordered by created_at desc."""
        q = (
            select(ChronoEntry)
            .where(ChronoEntry.user_id == str(user_id))
            .order_by(ChronoEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if from_date:
            q = q.where(ChronoEntry.created_at >= from_date)
        if to_date:
            q = q.where(ChronoEntry.created_at <= to_date)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def add_evidence(
        self,
        chrono_entry_id: str,
        text_snippet: str,
        message_id: str | None = None,
    ) -> Evidence:
        """Add evidence to a chrono entry."""
        evidence = Evidence(
            chrono_entry_id=chrono_entry_id,
            text_snippet=text_snippet,
            message_id=message_id,
        )
        self.session.add(evidence)
        await self.session.flush()
        return evidence
