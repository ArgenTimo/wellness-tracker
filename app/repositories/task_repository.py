"""Task reminder repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import TaskReminder


class TaskRepository:
    """Repository for task reminders."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        description: str,
        due_date: datetime | None = None,
        auto_generated: bool = False,
        status: str = "pending",
        clinic_id: str | None = None,
    ) -> TaskReminder:
        """Create a task reminder."""
        task = TaskReminder(
            user_id=user_id,
            description=description,
            due_date=due_date,
            auto_generated=auto_generated,
            status=status,
            clinic_id=clinic_id,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_user(
        self,
        user_id: str | UUID,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[TaskReminder]:
        """Get tasks for a user."""
        q = (
            select(TaskReminder)
            .where(TaskReminder.user_id == str(user_id))
            .order_by(TaskReminder.due_date.asc().nullslast(), TaskReminder.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            q = q.where(TaskReminder.status == status)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, task_id: str | UUID) -> TaskReminder | None:
        """Get task by ID."""
        result = await self.session.execute(
            select(TaskReminder).where(TaskReminder.id == str(task_id))
        )
        return result.scalar_one_or_none()

    async def update_status(
        self, task_id: str | UUID, status: str
    ) -> TaskReminder | None:
        """Update task status."""
        task = await self.get_by_id(task_id)
        if task:
            task.status = status
            await self.session.flush()
        return task
