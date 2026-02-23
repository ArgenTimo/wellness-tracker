"""Domain enumerations."""

import enum


class InviteType(str, enum.Enum):
    """Invitation type for linking users."""

    CLIENT_INVITE = "client_invite"
    SPECIALIST_INVITE = "specialist_invite"


class MessageRole(str, enum.Enum):
    """Chat message role."""

    CLIENT = "client"
    BOT = "bot"


class ScaleType(str, enum.Enum):
    """Metric value scale type."""

    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    CATEGORICAL = "categorical"


class TaskStatus(str, enum.Enum):
    """Task/reminder status."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
