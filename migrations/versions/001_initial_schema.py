"""Initial schema - all core entities.

Revision ID: 001_initial
Revises:
Create Date: 2025-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "specialists",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_specialists_email", "specialists", ["email"], unique=True)
    op.create_index("ix_specialists_clinic_id", "specialists", ["clinic_id"])

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("hashed_password", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("timezone", sa.Text(), nullable=True),
        sa.Column("preferences", postgresql.JSONB(), nullable=True),
        sa.Column("specialist_id", sa.UUID(), nullable=True),
        sa.Column("consent_flags", postgresql.JSONB(), nullable=True),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["specialist_id"], ["specialists.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_user_profiles_email", "user_profiles", ["email"], unique=True)
    op.create_index("ix_user_profiles_role", "user_profiles", ["role"])
    op.create_index("ix_user_profiles_specialist_id", "user_profiles", ["specialist_id"])
    op.create_index("ix_user_profiles_clinic_id", "user_profiles", ["clinic_id"])

    op.create_table(
        "metric_definitions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scale_type", sa.Text(), nullable=False),
        sa.Column("canonical_id", sa.UUID(), nullable=True),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_metric_definitions_name", "metric_definitions", ["name"])
    op.create_index("ix_metric_definitions_scale_type", "metric_definitions", ["scale_type"])
    op.create_index("ix_metric_definitions_clinic_id", "metric_definitions", ["clinic_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chat_messages_user_id", "chat_messages", ["user_id"])
    op.create_index("ix_chat_messages_role", "chat_messages", ["role"])

    op.create_table(
        "chrono_entries",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("metric_id", sa.UUID(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_hypothesis", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("source_message_id", sa.UUID(), nullable=True),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["metric_id"], ["metric_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_message_id"], ["chat_messages.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_chrono_entries_user_id", "chrono_entries", ["user_id"])
    op.create_index("ix_chrono_entries_metric_id", "chrono_entries", ["metric_id"])
    op.create_index("ix_chrono_entries_source_message_id", "chrono_entries", ["source_message_id"])
    op.create_index("ix_chrono_entries_clinic_id", "chrono_entries", ["clinic_id"])
    op.create_index("ix_chrono_user_created", "chrono_entries", ["user_id", "created_at"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("chrono_entry_id", sa.UUID(), nullable=False),
        sa.Column("text_snippet", sa.Text(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["chrono_entry_id"], ["chrono_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_evidence_chrono_entry_id", "evidence", ["chrono_entry_id"])
    op.create_index("ix_evidence_message_id", "evidence", ["message_id"])

    op.create_table(
        "task_reminders",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_generated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_task_reminders_user_id", "task_reminders", ["user_id"])
    op.create_index("ix_task_reminders_clinic_id", "task_reminders", ["clinic_id"])


def downgrade() -> None:
    op.drop_table("task_reminders")
    op.drop_table("evidence")
    op.drop_table("chrono_entries")
    op.drop_table("chat_messages")
    op.drop_table("metric_definitions")
    op.drop_table("user_profiles")
    op.drop_table("specialists")
