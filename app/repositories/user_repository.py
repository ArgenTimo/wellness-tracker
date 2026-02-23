"""User repository - single User entity."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import User


class UserRepository:
    """Repository for User data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        """Find user by email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str | UUID) -> User | None:
        """Find user by ID."""
        result = await self.session.execute(select(User).where(User.id == str(user_id)))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        name: str | None = None,
        age: int | None = None,
        language: str | None = None,
        timezone: str | None = None,
        clinic_id: str | None = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            name=name,
            age=age,
            language=language,
            timezone=timezone,
            clinic_id=clinic_id,
        )
        self.session.add(user)
        await self.session.flush()
        return user
