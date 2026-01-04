"""Forecast service for net worth projections."""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.transaction import Transaction
from app.services.net_worth import NetWorthService
from app.schemas.analysis import ForecastResponse, ForecastPoint


class ForecastService:
    """Service for forecasting net worth over time."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.net_worth_service = NetWorthService(session)

    async def _average_monthly_net(self, user_id: int, months: int = 6) -> Decimal:
        """Compute average monthly net cashflow."""
        end = datetime.utcnow()
        start = end - timedelta(days=30 * months)

        result = await self.session.execute(
            select(
                func.date_trunc("month", Transaction.transaction_date).label("month"),
                func.sum(Transaction.amount).label("net"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start,
            )
            .group_by("month")
            .order_by("month")
        )
        rows = result.all()
        if not rows:
            return Decimal("0")

        total = sum(Decimal(str(row.net or 0)) for row in rows)
        return total / Decimal(len(rows))

    async def generate_forecast(
        self,
        user_id: int,
        years: int,
        monthly_contribution: Decimal | None,
        annual_return_rate: float,
    ) -> ForecastResponse:
        """Generate net worth forecast for a time horizon."""
        summary = await self.net_worth_service.get_net_worth_summary(user_id)
        average_monthly_net = await self._average_monthly_net(user_id)
        contribution = monthly_contribution if monthly_contribution is not None else average_monthly_net

        monthly_rate = (1 + annual_return_rate / 100) ** (1 / 12) - 1
        monthly_rate_decimal = Decimal(str(monthly_rate))

        net_worth = Decimal(str(summary.net_worth))
        projection = []
        current_year = datetime.utcnow().year
        total_months = years * 12

        for month in range(1, total_months + 1):
            net_worth = (net_worth + contribution) * (Decimal("1") + monthly_rate_decimal)
            if month % 12 == 0:
                projection.append(
                    ForecastPoint(
                        year=current_year + month // 12,
                        net_worth=net_worth,
                    )
                )

        return ForecastResponse(
            start_net_worth=Decimal(str(summary.net_worth)),
            monthly_contribution=contribution,
            annual_return_rate=annual_return_rate,
            average_monthly_net=average_monthly_net,
            projection=projection,
        )
