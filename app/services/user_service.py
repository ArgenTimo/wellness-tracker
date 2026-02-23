"""User and authentication service."""

from app.core.security import get_password_hash, verify_password
from app.db.session import DbSession
from app.domain.schemas import RegisterRequest
from app.domain.models import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Handles user registration and auth."""

    def __init__(self, session: DbSession):
        self.repo = UserRepository(session)

    async def register(
        self, data: RegisterRequest, clinic_id: str | None = None
    ) -> User:
        """Register a new user (standalone, no specialist required)."""
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ValueError("User with this email already exists")
        return await self.repo.create(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            name=data.name,
            age=data.age,
            language=data.language,
            timezone=data.timezone,
            clinic_id=clinic_id,
        )

    async def authenticate(self, email: str, password: str) -> User:
        """
        Authenticate user. Returns User.
        Raises ValueError if credentials invalid.
        """
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        return user
