"""Analytics and summary service - stub implementation."""

from datetime import datetime, timedelta

from app.db.session import DbSession
from app.domain.schemas import SummaryResponse


class AnalyticsService:
    """
    Analytics service - stub for future implementation.
    Will aggregate chrono entries, compute metrics, generate insights.
    """

    def __init__(self, session: DbSession):
        self.session = session

    async def get_summary(
        self,
        user_id: str,
        period_days: int = 7,
    ) -> SummaryResponse:
        """
        Get wellness summary for a user.
        Stub: returns empty structure. Real implementation will:
        - Aggregate chrono entries by metric
        - Compute trends, averages
        - Run LLM insight extraction
        """
        now = datetime.utcnow()
        period_end = now
        period_start = now - timedelta(days=period_days)
        return SummaryResponse(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            metrics={},
            insights=[],
        )
