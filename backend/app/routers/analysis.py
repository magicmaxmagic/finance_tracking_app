"""Analysis router for forecasting endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.core.deps import get_current_user_id
from app.schemas.analysis import ForecastRequest, ForecastResponse
from app.services.forecast import ForecastService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/forecast", response_model=ForecastResponse)
async def forecast_net_worth(
    payload: ForecastRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Generate a net worth forecast."""
    service = ForecastService(session)
    try:
        return await service.generate_forecast(
            user_id=user_id,
            years=payload.years,
            monthly_contribution=payload.monthly_contribution,
            annual_return_rate=payload.annual_return_rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
