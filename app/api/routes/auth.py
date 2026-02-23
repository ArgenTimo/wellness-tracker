"""Authentication routes - single User entity."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.core.security import create_access_token, create_refresh_token
from app.db.session import DbSession
from app.domain.schemas import LoginRequest, RegisterRequest, Token, UserResponse
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(data: RegisterRequest, session: DbSession):
    """Register a new user (standalone, no specialist required)."""
    service = UserService(session)
    try:
        user = await service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, session: DbSession):
    """Login for any user."""
    service = UserService(session)
    try:
        user = await service.authenticate(data.email, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return Token(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
async def get_me(current: CurrentUser, session: DbSession):
    """Get current user profile."""
    repo = UserRepository(session)
    user = await repo.get_by_id(current)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)
