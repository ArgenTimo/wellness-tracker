"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.enums import MessageRole, ScaleType, TaskStatus


# ----- Auth -----


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    exp: datetime
    type: str = "access"


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register user request (single entity for specialist and client)."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str | None = None
    age: int | None = None
    language: str | None = None
    timezone: str | None = None


# ----- User -----


class UserResponse(BaseModel):
    """User API response."""

    id: str
    email: str
    name: str | None = None
    age: int | None = None
    language: str | None = None
    timezone: str | None = None
    preferences: dict[str, Any] | None = None
    consent_flags: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ----- Links / Invites -----


class ClientInviteRequest(BaseModel):
    """Request body for client invite (optional single_use override)."""

    single_use: bool = False


class ClientInviteResponse(BaseModel):
    """Client invite response with token and URL."""

    token: str
    url: str


class SpecialistInviteResponse(BaseModel):
    """Specialist invite response - always single-use."""

    token: str
    url: str


class RedeemResponse(BaseModel):
    """Redeem token response."""

    status: str  # "linked" | "already_linked" | "ignored_self_redeem"


# ----- Metric -----


class MetricDefinitionBase(BaseModel):
    """Base metric definition schema."""

    name: str
    description: str | None = None
    scale_type: ScaleType


class MetricDefinitionResponse(MetricDefinitionBase):
    """Metric definition API response."""

    id: str
    canonical_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ----- Chrono Entry -----


class ChronoEntryCreate(BaseModel):
    """Create chrono entry request."""

    metric_id: str
    value: str | int | float | bool
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    is_hypothesis: bool = False
    source_message_id: str | None = None

    @field_validator("value", mode="before")
    @classmethod
    def coerce_value(cls, v: Any) -> str:
        """Coerce value to string for storage."""
        return str(v)


class ChronoEntryResponse(BaseModel):
    """Chrono entry API response."""

    id: str
    user_id: str
    metric_id: str
    value: str
    confidence: float
    is_hypothesis: bool
    source_message_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceResponse(BaseModel):
    """Evidence API response."""

    id: str
    chrono_entry_id: str
    text_snippet: str
    message_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ----- Chat -----


class ChatMessageCreate(BaseModel):
    """Create chat message request."""

    role: MessageRole
    content: str


class ChatMessageResponse(BaseModel):
    """Chat message API response."""

    id: str
    user_id: str
    role: str
    content: str
    timestamp: datetime

    model_config = {"from_attributes": True}


# ----- Task -----


class TaskReminderCreate(BaseModel):
    """Create task reminder request."""

    description: str
    due_date: datetime | None = None
    auto_generated: bool = False


class TaskReminderResponse(BaseModel):
    """Task reminder API response."""

    id: str
    user_id: str
    description: str
    due_date: datetime | None = None
    auto_generated: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskReminderUpdate(BaseModel):
    """Update task reminder request."""

    status: TaskStatus | None = None
    description: str | None = None


# ----- Summary (Analytics stub) -----


class SummaryResponse(BaseModel):
    """Wellness summary response - stub structure."""

    user_id: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    insights: list[str] = Field(default_factory=list)
