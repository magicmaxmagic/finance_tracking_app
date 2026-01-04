"""Repository for scenario modeling."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models.scenario import Scenario, ScenarioAction


class ScenarioRepository:
    """Scenario repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, scenario_id: int, user_id: int) -> Scenario | None:
        result = await self.session.execute(
            select(Scenario)
            .options(selectinload(Scenario.actions))
            .where(Scenario.id == scenario_id, Scenario.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int, active_only: bool = True) -> list[Scenario]:
        query = select(Scenario).options(selectinload(Scenario.actions)).where(Scenario.user_id == user_id)
        if active_only:
            query = query.where(Scenario.is_active == True)
        query = query.order_by(Scenario.updated_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_group(self, scenario_group_id: str, user_id: int) -> Scenario | None:
        result = await self.session.execute(
            select(Scenario)
            .where(
                Scenario.scenario_group_id == scenario_group_id,
                Scenario.user_id == user_id,
            )
            .order_by(Scenario.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def deactivate_group(self, scenario_group_id: str, user_id: int) -> None:
        await self.session.execute(
            update(Scenario)
            .where(
                Scenario.scenario_group_id == scenario_group_id,
                Scenario.user_id == user_id,
            )
            .values(is_active=False)
        )

    async def set_group_baseline(self, scenario_group_id: str, user_id: int, baseline_id: int) -> None:
        await self.session.execute(
            update(Scenario)
            .where(
                Scenario.scenario_group_id == scenario_group_id,
                Scenario.user_id == user_id,
            )
            .values(is_baseline=False)
        )
        await self.session.execute(
            update(Scenario)
            .where(
                Scenario.id == baseline_id,
                Scenario.user_id == user_id,
            )
            .values(is_baseline=True)
        )

    async def create(self, user_id: int, **kwargs) -> Scenario:
        actions = kwargs.pop("actions", [])
        scenario = Scenario(user_id=user_id, **kwargs)
        for action in actions:
            scenario.actions.append(ScenarioAction(**action))
        self.session.add(scenario)
        await self.session.commit()
        await self.session.refresh(scenario)
        return scenario

    async def delete(self, scenario_id: int, user_id: int) -> bool:
        scenario = await self.get_by_id(scenario_id, user_id)
        if not scenario:
            return False
        await self.session.delete(scenario)
        await self.session.commit()
        return True
