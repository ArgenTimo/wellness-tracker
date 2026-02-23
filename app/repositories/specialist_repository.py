"""Specialist-scoped queries - derived from user_access_links."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User
from app.repositories.access_link_repository import AccessLinkRepository


class SpecialistRepository:
    """Repository for specialist-scoped queries (access link based)."""

    def __init__(self, session: AsyncSession):
        self.link_repo = AccessLinkRepository(session)

    async def get_specialist_clients(
        self, specialist_user_id: str | UUID
    ) -> list[User]:
        """Get all clients for a specialist (from access links)."""
        return await self.link_repo.get_clients_for_specialist(specialist_user_id)
