"""SQLAlchemy ORM models - domain entities."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


def gen_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid4())


class User(Base):
    """
    Single user entity. Specialist and client are the same - a specialist
    is a user with access links to other users.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    language: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    consent_flags: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    clinic_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    chrono_entries: Mapped[list["ChronoEntry"]] = relationship(
        "ChronoEntry", back_populates="user"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="user"
    )
    task_reminders: Mapped[list["TaskReminder"]] = relationship(
        "TaskReminder", back_populates="user"
    )
    # Access links where this user is the specialist
    specialist_links: Mapped[list["UserAccessLink"]] = relationship(
        "UserAccessLink",
        back_populates="specialist_user",
        foreign_keys="UserAccessLink.specialist_user_id",
    )
    # Access links where this user is the client
    client_links: Mapped[list["UserAccessLink"]] = relationship(
        "UserAccessLink",
        back_populates="client_user",
        foreign_keys="UserAccessLink.client_user_id",
    )
    # Invitations created by this user
    created_invites: Mapped[list["InviteToken"]] = relationship(
        "InviteToken", back_populates="inviter", foreign_keys="InviteToken.inviter_user_id"
    )


class UserAccessLink(Base):
    """
    M2M access link: specialist can view client data.
    Single source of truth for specialist-client relationships.
    """

    __tablename__ = "user_access_links"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    specialist_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    specialist_user: Mapped["User"] = relationship(
        "User",
        back_populates="specialist_links",
        foreign_keys=[specialist_user_id],
    )
    client_user: Mapped["User"] = relationship(
        "User",
        back_populates="client_links",
        foreign_keys=[client_user_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "specialist_user_id", "client_user_id", name="uq_specialist_client"
        ),
    )


class InviteToken(Base):
    """Invitation token for linking specialist and client."""

    __tablename__ = "invite_tokens"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    inviter_user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invite_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    single_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    used_by_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    inviter: Mapped["User"] = relationship(
        "User", back_populates="created_invites", foreign_keys=[inviter_user_id]
    )


class MetricDefinition(Base):
    """Metric definition for wellness tracking."""

    __tablename__ = "metric_definitions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scale_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    canonical_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )
    clinic_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    chrono_entries: Mapped[list["ChronoEntry"]] = relationship(
        "ChronoEntry", back_populates="metric"
    )


class ChatMessage(Base):
    """Chat message - stores conversation for evidence linking."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="chat_messages")
    chrono_entries: Mapped[list["ChronoEntry"]] = relationship(
        "ChronoEntry",
        back_populates="source_message",
        foreign_keys="ChronoEntry.source_message_id",
    )


class ChronoEntry(Base):
    """Chronological metric entry with confidence and evidence link."""

    __tablename__ = "chrono_entries"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("metric_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_hypothesis: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_message_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("chat_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    clinic_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="chrono_entries")
    metric: Mapped["MetricDefinition"] = relationship(
        "MetricDefinition", back_populates="chrono_entries"
    )
    source_message: Mapped["ChatMessage | None"] = relationship(
        "ChatMessage", back_populates="chrono_entries", foreign_keys=[source_message_id]
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="chrono_entry", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_chrono_user_created", "user_id", "created_at"),)


class Evidence(Base):
    """Evidence snippet linking to a chrono entry."""

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    chrono_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("chrono_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    message_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("chat_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    chrono_entry: Mapped["ChronoEntry"] = relationship(
        "ChronoEntry", back_populates="evidence"
    )


class TaskReminder(Base):
    """Task or reminder for user."""

    __tablename__ = "task_reminders"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=gen_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    clinic_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="task_reminders")
