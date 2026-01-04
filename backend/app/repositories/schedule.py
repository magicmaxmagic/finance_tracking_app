"""Schedule repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.schedule_block import ScheduleBlock


class ScheduleRepository:
    """Repository for schedule block operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, block_id: int, user_id: int) -> ScheduleBlock | None:
        """Get schedule block by ID (ensure user ownership)."""
        result = await self.session.execute(
            select(ScheduleBlock).where(
                ScheduleBlock.id == block_id,
                ScheduleBlock.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> list[ScheduleBlock]:
        """Get all schedule blocks for user."""
        result = await self.session.execute(
            select(ScheduleBlock)
            .where(ScheduleBlock.user_id == user_id)
            .order_by(ScheduleBlock.day_of_week, ScheduleBlock.start_time)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        """Count schedule blocks for user."""
        result = await self.session.execute(
            select(func.count(ScheduleBlock.id)).where(ScheduleBlock.user_id == user_id)
        )
        return int(result.scalar() or 0)

    async def create(self, user_id: int, **kwargs) -> ScheduleBlock:
        """Create a new schedule block."""
        block = ScheduleBlock(user_id=user_id, **kwargs)
        self.session.add(block)
        await self.session.commit()
        await self.session.refresh(block)
        return block

    async def create_bulk(self, user_id: int, blocks: list[dict]) -> list[ScheduleBlock]:
        """Create multiple schedule blocks."""
        schedule_blocks = [ScheduleBlock(user_id=user_id, **data) for data in blocks]
        self.session.add_all(schedule_blocks)
        await self.session.commit()
        for block in schedule_blocks:
            await self.session.refresh(block)
        return schedule_blocks

    async def update(self, block_id: int, user_id: int, **kwargs) -> ScheduleBlock | None:
        """Update a schedule block."""
        block = await self.get_by_id(block_id, user_id)
        if not block:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(block, key, value)

        self.session.add(block)
        await self.session.commit()
        await self.session.refresh(block)
        return block

    async def delete(self, block_id: int, user_id: int) -> bool:
        """Delete a schedule block."""
        block = await self.get_by_id(block_id, user_id)
        if not block:
            return False

        await self.session.delete(block)
        await self.session.commit()
        return True
