"""Investment service for asset operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.investment import InvestmentRepository
from app.schemas.investment import InvestmentResponse


class InvestmentService:
    """Service for investment asset operations."""

    def __init__(self, session: AsyncSession):
        self.repository = InvestmentRepository(session)
        self.session = session

    async def get_investment(self, investment_id: int, user_id: int) -> InvestmentResponse:
        """Get investment asset by ID."""
        investment = await self.repository.get_by_id(investment_id, user_id)
        if not investment:
            raise ValueError("Investment asset not found")
        return InvestmentResponse.from_orm(investment)

    async def get_all_investments(self, user_id: int) -> list[InvestmentResponse]:
        """Get all investment assets for user."""
        investments = await self.repository.get_all_by_user(user_id)
        return [InvestmentResponse.from_orm(asset) for asset in investments]

    async def create_investment(self, user_id: int, **kwargs) -> InvestmentResponse:
        """Create a new investment asset."""
        investment = await self.repository.create(user_id=user_id, **kwargs)
        return InvestmentResponse.from_orm(investment)

    async def update_investment(
        self, investment_id: int, user_id: int, **kwargs
    ) -> InvestmentResponse:
        """Update investment asset."""
        investment = await self.repository.update(investment_id, user_id, **kwargs)
        if not investment:
            raise ValueError("Investment asset not found")
        return InvestmentResponse.from_orm(investment)

    async def delete_investment(self, investment_id: int, user_id: int) -> bool:
        """Delete investment asset."""
        success = await self.repository.delete(investment_id, user_id)
        if not success:
            raise ValueError("Investment asset not found")
        return success
