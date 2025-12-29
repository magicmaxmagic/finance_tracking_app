"""FX rate service."""
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.fx_rate import FXRateRepository
from app.schemas.fx_rate import FXRateResponse


class FXRateService:
    """Service for FX rates."""

    def __init__(self, session: AsyncSession):
        self.repository = FXRateRepository(session)
        self.session = session

    async def upsert_rate(self, base_currency: str, quote_currency: str, rate: float, as_of: date) -> FXRateResponse:
        fx_rate = await self.repository.upsert(base_currency, quote_currency, rate, as_of)
        return FXRateResponse.from_orm(fx_rate)

    async def get_rate(self, base_currency: str, quote_currency: str, as_of: date) -> FXRateResponse | None:
        fx_rate = await self.repository.get_rate(base_currency, quote_currency, as_of)
        if not fx_rate:
            return None
        return FXRateResponse.from_orm(fx_rate)
