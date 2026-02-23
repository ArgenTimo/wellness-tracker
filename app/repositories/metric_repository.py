"""Metric definition repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import MetricDefinition


class MetricRepository:
    """Repository for metric definitions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, metric_id: str | UUID) -> MetricDefinition | None:
        """Get metric definition by ID."""
        result = await self.session.execute(
            select(MetricDefinition).where(MetricDefinition.id == str(metric_id))
        )
        return result.scalar_one_or_none()
