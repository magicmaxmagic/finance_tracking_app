"""Scenario service for strategy modeling."""
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.scenario import ScenarioRepository
from app.schemas.scenario import ScenarioResponse


class ScenarioService:
    """Service for scenario operations."""

    def __init__(self, session: AsyncSession):
        self.repository = ScenarioRepository(session)
        self.session = session

    async def get_scenario(self, scenario_id: int, user_id: int) -> ScenarioResponse:
        scenario = await self.repository.get_by_id(scenario_id, user_id)
        if not scenario:
            raise ValueError("Scenario not found")
        return ScenarioResponse.from_orm(scenario)

    async def get_all_scenarios(self, user_id: int) -> list[ScenarioResponse]:
        scenarios = await self.repository.get_all_by_user(user_id)
        return [ScenarioResponse.from_orm(s) for s in scenarios]

    async def create_scenario(self, user_id: int, **kwargs) -> ScenarioResponse:
        actions = kwargs.pop("actions", [])
        scenario_group_id = kwargs.pop("scenario_group_id", None) or str(uuid4())
        latest = await self.repository.get_latest_by_group(scenario_group_id, user_id)
        version = (latest.version + 1) if latest else 1
        if latest:
            await self.repository.deactivate_group(scenario_group_id, user_id)
        action_payloads = self._normalize_actions(actions)
        scenario = await self.repository.create(
            user_id=user_id,
            scenario_group_id=scenario_group_id,
            version=version,
            is_active=True,
            actions=action_payloads,
            **kwargs,
        )
        if scenario.is_baseline:
            await self.repository.set_group_baseline(scenario_group_id, user_id, scenario.id)
            await self.session.commit()
        return ScenarioResponse.from_orm(scenario)

    async def update_scenario(self, scenario_id: int, user_id: int, **kwargs) -> ScenarioResponse:
        existing = await self.repository.get_by_id(scenario_id, user_id)
        if not existing:
            raise ValueError("Scenario not found")

        actions = kwargs.pop("actions", None)
        scenario_group_id = existing.scenario_group_id
        version = existing.version + 1

        await self.repository.deactivate_group(scenario_group_id, user_id)
        action_payloads = self._normalize_actions(actions) if actions is not None else None

        scenario = await self.repository.create(
            user_id=user_id,
            scenario_group_id=scenario_group_id,
            version=version,
            is_active=True,
            name=kwargs.get("name") or existing.name,
            description=kwargs.get("description") if "description" in kwargs else existing.description,
            goal_id=kwargs.get("goal_id") if "goal_id" in kwargs else existing.goal_id,
            assumption_id=kwargs.get("assumption_id") if "assumption_id" in kwargs else existing.assumption_id,
            is_baseline=kwargs.get("is_baseline") if "is_baseline" in kwargs else existing.is_baseline,
            actions=action_payloads if action_payloads is not None else [
                {
                    "action_type": action.action_type,
                    "value": action.value,
                    "start_date": action.start_date,
                    "end_date": action.end_date,
                }
                for action in existing.actions
            ],
        )

        if scenario.is_baseline:
            await self.repository.set_group_baseline(scenario_group_id, user_id, scenario.id)
            await self.session.commit()
        return ScenarioResponse.from_orm(scenario)

    async def delete_scenario(self, scenario_id: int, user_id: int) -> bool:
        success = await self.repository.delete(scenario_id, user_id)
        if not success:
            raise ValueError("Scenario not found")
        return success

    def _normalize_actions(self, actions):
        return [
            action.dict() if hasattr(action, "dict") else action
            for action in (actions or [])
        ]
