"""FX rate repository."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from app.models.fx_rate import FXRate


class FXRateRepository:
    """Repository for FX rates."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, base_currency: str, quote_currency: str, rate: float, as_of: date) -> FXRate:
        result = await self.session.execute(
            select(FXRate).where(
                FXRate.base_currency == base_currency,
                FXRate.quote_currency == quote_currency,
                FXRate.as_of == as_of,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.rate = rate
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        fx_rate = FXRate(base_currency=base_currency, quote_currency=quote_currency, rate=rate, as_of=as_of)
        self.session.add(fx_rate)
        await self.session.commit()
        await self.session.refresh(fx_rate)
        return fx_rate

    async def get_rate(self, base_currency: str, quote_currency: str, as_of: date) -> FXRate | None:
        result = await self.session.execute(
            select(FXRate).where(
                FXRate.base_currency == base_currency,
                FXRate.quote_currency == quote_currency,
                FXRate.as_of == as_of,
            )
        )
        return result.scalar_one_or_none()
