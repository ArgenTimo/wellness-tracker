"""Links (invites, redeem) service."""

import hashlib
import secrets
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.session import DbSession
from app.domain.enums import InviteType
from app.domain.models import UserAccessLink
from app.repositories.access_link_repository import AccessLinkRepository


class LinksService:
    """Handles invite creation and token redemption."""

    def __init__(self, session: DbSession):
        self.repo = AccessLinkRepository(session)

    def _hash_token(self, token: str) -> str:
        """Hash token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_token(self) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(32)

    def _build_url(self, token: str) -> str:
        """Build full redeem URL."""
        base = get_settings().invite_base_url.rstrip("/")
        return f"{base}?token={token}"

    async def create_client_invite(
        self, inviter_user_id: str, single_use: bool = False
    ) -> tuple[str, str]:
        """Create client invite. Returns (token, url)."""
        token = self._generate_token()
        token_hash = self._hash_token(token)
        await self.repo.create_invite_token(
            inviter_user_id=inviter_user_id,
            token_hash=token_hash,
            invite_type=InviteType.CLIENT_INVITE,
            single_use=single_use,
        )
        return token, self._build_url(token)

    async def create_specialist_invite(self, inviter_user_id: str) -> tuple[str, str]:
        """Create specialist invite. Must be single-use."""
        token = self._generate_token()
        token_hash = self._hash_token(token)
        await self.repo.create_invite_token(
            inviter_user_id=inviter_user_id,
            token_hash=token_hash,
            invite_type=InviteType.SPECIALIST_INVITE,
            single_use=True,
        )
        return token, self._build_url(token)

    async def redeem_token(
        self, raw_token: str, redeemer_user_id: str
    ) -> str:
        """
        Redeem invite token. Returns status: "linked" | "already_linked" | "ignored_self_redeem".
        Raises ValueError for expired or already-used single-use.
        """
        token_hash = self._hash_token(raw_token)
        invite = await self.repo.find_token_by_hash(token_hash)
        if not invite:
            raise ValueError("Invalid token")

        now = datetime.now(timezone.utc)
        if invite.expires_at and invite.expires_at < now:
            raise ValueError("Token expired")

        if invite.single_use and invite.used_at is not None:
            raise ValueError("Token already used")

        if invite.inviter_user_id == redeemer_user_id:
            return "ignored_self_redeem"

        if invite.invite_type == InviteType.CLIENT_INVITE.value:
            specialist_id = invite.inviter_user_id
            client_id = redeemer_user_id
        else:  # specialist_invite
            specialist_id = redeemer_user_id
            client_id = invite.inviter_user_id

        existing = await self.repo.get_active_link(specialist_id, client_id)
        if existing:
            return "already_linked"

        await self.repo.create_link(specialist_id, client_id)

        if invite.single_use:
            await self.repo.mark_token_used(invite.id, redeemer_user_id)

        return "linked"
