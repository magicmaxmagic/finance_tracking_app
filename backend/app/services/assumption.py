"""Assumption version service."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.assumption import AssumptionRepository
from app.schemas.assumption import AssumptionResponse


class AssumptionService:
    """Service for assumption versions."""

    def __init__(self, session: AsyncSession):
        self.repository = AssumptionRepository(session)
        self.session = session

    async def get_assumption(self, assumption_id: int, user_id: int) -> AssumptionResponse:
        assumption = await self.repository.get_by_id(assumption_id, user_id)
        if not assumption:
            raise ValueError("Assumption not found")
        return AssumptionResponse.from_orm(assumption)

    async def get_all_assumptions(self, user_id: int) -> list[AssumptionResponse]:
        assumptions = await self.repository.get_all_by_user(user_id)
        return [AssumptionResponse.from_orm(a) for a in assumptions]

    async def get_active_assumption(self, user_id: int) -> AssumptionResponse | None:
        assumption = await self.repository.get_active(user_id)
        return AssumptionResponse.from_orm(assumption) if assumption else None

    async def create_assumption(self, user_id: int, **kwargs) -> AssumptionResponse:
        latest = await self.repository.get_latest_version(user_id)
        next_version = (latest.version + 1) if latest else 1
        await self.repository.deactivate_all(user_id)
        assumption = await self.repository.create(user_id=user_id, version=next_version, is_active=True, **kwargs)
        return AssumptionResponse.from_orm(assumption)

    async def activate_assumption(self, assumption_id: int, user_id: int) -> AssumptionResponse:
        assumption = await self.repository.get_by_id(assumption_id, user_id)
        if not assumption:
            raise ValueError("Assumption not found")
        await self.repository.deactivate_all(user_id)
        assumption.is_active = True
        self.session.add(assumption)
        await self.session.commit()
        await self.session.refresh(assumption)
        return AssumptionResponse.from_orm(assumption)
