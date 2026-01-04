"""Repository for assumption versions."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.assumption import AssumptionVersion


class AssumptionRepository:
    """Assumption version repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, assumption_id: int, user_id: int) -> AssumptionVersion | None:
        result = await self.session.execute(
            select(AssumptionVersion).where(
                AssumptionVersion.id == assumption_id,
                AssumptionVersion.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> list[AssumptionVersion]:
        result = await self.session.execute(
            select(AssumptionVersion)
            .where(AssumptionVersion.user_id == user_id)
            .order_by(AssumptionVersion.version.desc())
        )
        return list(result.scalars().all())

    async def get_latest_version(self, user_id: int) -> AssumptionVersion | None:
        result = await self.session.execute(
            select(AssumptionVersion)
            .where(AssumptionVersion.user_id == user_id)
            .order_by(AssumptionVersion.version.desc())
        )
        return result.scalars().first()

    async def get_active(self, user_id: int) -> AssumptionVersion | None:
        result = await self.session.execute(
            select(AssumptionVersion)
            .where(AssumptionVersion.user_id == user_id, AssumptionVersion.is_active == True)
        )
        return result.scalars().first()

    async def deactivate_all(self, user_id: int) -> None:
        await self.session.execute(
            update(AssumptionVersion)
            .where(AssumptionVersion.user_id == user_id, AssumptionVersion.is_active == True)
            .values(is_active=False)
        )
        await self.session.commit()

    async def create(self, user_id: int, **kwargs) -> AssumptionVersion:
        assumption = AssumptionVersion(user_id=user_id, **kwargs)
        self.session.add(assumption)
        await self.session.commit()
        await self.session.refresh(assumption)
        return assumption
