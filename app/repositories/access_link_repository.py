"""User access links and invite tokens repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import InviteType
from app.domain.models import InviteToken, User, UserAccessLink


class AccessLinkRepository:
    """Repository for user_access_links and invite_tokens."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_link(
        self, specialist_user_id: str | UUID, client_user_id: str | UUID
    ) -> UserAccessLink | None:
        """Get active access link between specialist and client."""
        result = await self.session.execute(
            select(UserAccessLink).where(
                UserAccessLink.specialist_user_id == str(specialist_user_id),
                UserAccessLink.client_user_id == str(client_user_id),
                UserAccessLink.status == "active",
                UserAccessLink.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create_link(
        self, specialist_user_id: str, client_user_id: str
    ) -> UserAccessLink:
        """Create access link. Idempotent - returns existing if present."""
        existing = await self.get_active_link(specialist_user_id, client_user_id)
        if existing:
            return existing
        link = UserAccessLink(
            specialist_user_id=str(specialist_user_id),
            client_user_id=str(client_user_id),
        )
        self.session.add(link)
        await self.session.flush()
        return link

    async def get_clients_for_specialist(
        self, specialist_user_id: str | UUID
    ) -> list[User]:
        """Get all clients linked to a specialist."""
        result = await self.session.execute(
            select(User).join(
                UserAccessLink,
                UserAccessLink.client_user_id == User.id,
            ).where(
                UserAccessLink.specialist_user_id == str(specialist_user_id),
                UserAccessLink.status == "active",
                UserAccessLink.revoked_at.is_(None),
            )
        )
        return list(result.scalars().unique().all())

    async def has_specialist_access(
        self, specialist_user_id: str | UUID, client_user_id: str | UUID
    ) -> bool:
        """Check if specialist has active access to client."""
        link = await self.get_active_link(specialist_user_id, client_user_id)
        return link is not None

    async def create_invite_token(
        self,
        inviter_user_id: str,
        token_hash: str,
        invite_type: InviteType,
        single_use: bool = False,
        expires_at: datetime | None = None,
    ) -> InviteToken:
        """Create invite token record."""
        token = InviteToken(
            token_hash=token_hash,
            inviter_user_id=inviter_user_id,
            invite_type=invite_type.value,
            single_use=single_use,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def find_token_by_hash(self, token_hash: str) -> InviteToken | None:
        """Find invite token by hash."""
        result = await self.session.execute(
            select(InviteToken).where(InviteToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_token_used(
        self, token_id: str, used_by_user_id: str
    ) -> None:
        """Mark token as used."""
        result = await self.session.execute(
            select(InviteToken).where(InviteToken.id == token_id)
        )
        token = result.scalar_one_or_none()
        if token:
            from datetime import datetime, timezone

            token.used_at = datetime.now(timezone.utc)
            token.used_by_user_id = used_by_user_id
            await self.session.flush()
