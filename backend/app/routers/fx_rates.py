"""FX rates router."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.fx_rate import FXRateUpsert, FXRateResponse
from app.services.fx_rate import FXRateService
from app.core.deps import get_current_user_id

router = APIRouter(prefix="/api/fx-rates", tags=["fx-rates"])


@router.post("", response_model=FXRateResponse)
async def upsert_fx_rate(
    payload: FXRateUpsert,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = FXRateService(session)
    return await service.upsert_rate(
        base_currency=payload.base_currency.upper(),
        quote_currency=payload.quote_currency.upper(),
        rate=payload.rate,
        as_of=payload.as_of,
    )


@router.get("", response_model=FXRateResponse)
async def get_fx_rate(
    base_currency: str = Query(...),
    quote_currency: str = Query(...),
    as_of: date = Query(...),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    service = FXRateService(session)
    rate = await service.get_rate(base_currency.upper(), quote_currency.upper(), as_of)
    if not rate:
        raise HTTPException(status_code=404, detail="Rate not found")
    return rate
