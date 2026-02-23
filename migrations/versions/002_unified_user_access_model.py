"""Unified User model, user_access_links, invite_tokens.

Replaces Specialist table. Single User entity. Access via M2M links.
Revises: 001_initial
Create Date: 2025-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_unified_user"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table (merged from specialists + user_profiles)
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("timezone", sa.Text(), nullable=True),
        sa.Column("preferences", postgresql.JSONB(), nullable=True),
        sa.Column("consent_flags", postgresql.JSONB(), nullable=True),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_clinic_id", "users", ["clinic_id"])

    # Migrate specialists -> users
    op.execute("""
        INSERT INTO users (id, email, hashed_password, name, clinic_id, created_at)
        SELECT id, email, hashed_password, name, clinic_id, created_at
        FROM specialists
    """)

    # Migrate user_profiles -> users (clients, different ids)
    op.execute("""
        INSERT INTO users (id, email, hashed_password, name, age, language, timezone,
                          preferences, consent_flags, clinic_id, created_at)
        SELECT id, COALESCE(email, id::text || '@migrated.local'), COALESCE(hashed_password, ''),
               NULL, age, language, timezone, preferences, consent_flags, clinic_id, created_at
        FROM user_profiles
    """)

    # Create user_access_links from old specialist_id
    op.create_table(
        "user_access_links",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("specialist_user_id", sa.UUID(), nullable=False),
        sa.Column("client_user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["specialist_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("specialist_user_id", "client_user_id", name="uq_specialist_client"),
    )
    op.create_index("ix_user_access_links_specialist", "user_access_links", ["specialist_user_id"])
    op.create_index("ix_user_access_links_client", "user_access_links", ["client_user_id"])

    op.execute("""
        INSERT INTO user_access_links (id, specialist_user_id, client_user_id, status, created_at)
        SELECT gen_random_uuid(), specialist_id, user_profiles.id, 'active', NOW()
        FROM user_profiles
        WHERE specialist_id IS NOT NULL
    """)

    # Create invite_tokens
    op.create_table(
        "invite_tokens",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("inviter_user_id", sa.UUID(), nullable=False),
        sa.Column("invite_type", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("single_use", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_by_user_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["inviter_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_invite_tokens_token_hash", "invite_tokens", ["token_hash"])
    op.create_index("ix_invite_tokens_inviter", "invite_tokens", ["inviter_user_id"])

    # Update chrono_entries, chat_messages, task_reminders to reference users
    op.drop_constraint(
        "chrono_entries_user_id_fkey", "chrono_entries", type_="foreignkey"
    )
    op.create_foreign_key(
        "chrono_entries_user_id_fkey",
        "chrono_entries",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "chat_messages_user_id_fkey", "chat_messages", type_="foreignkey"
    )
    op.create_foreign_key(
        "chat_messages_user_id_fkey",
        "chat_messages",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "task_reminders_user_id_fkey", "task_reminders", type_="foreignkey"
    )
    op.create_foreign_key(
        "task_reminders_user_id_fkey",
        "task_reminders",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop old tables
    op.drop_table("user_profiles")
    op.drop_table("specialists")


def downgrade() -> None:
    # Recreate specialists and user_profiles (simplified - data loss on specialist_id)
    op.create_table(
        "specialists",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), server_default="false"),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_specialists_email", "specialists", ["email"], unique=True)

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

    # Revert FKs to user_profiles
    op.drop_constraint("chrono_entries_user_id_fkey", "chrono_entries", type_="foreignkey")
    op.create_foreign_key(
        "chrono_entries_user_id_fkey", "chrono_entries", "user_profiles",
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.drop_constraint("chat_messages_user_id_fkey", "chat_messages", type_="foreignkey")
    op.create_foreign_key(
        "chat_messages_user_id_fkey", "chat_messages", "user_profiles",
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.drop_constraint("task_reminders_user_id_fkey", "task_reminders", type_="foreignkey")
    op.create_foreign_key(
        "task_reminders_user_id_fkey", "task_reminders", "user_profiles",
        ["user_id"], ["id"], ondelete="CASCADE"
    )

    op.drop_table("invite_tokens")
    op.drop_table("user_access_links")
    op.drop_table("users")
