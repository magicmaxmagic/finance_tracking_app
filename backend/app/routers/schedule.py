"""Schedule router for schedule block management and exports."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.core.deps import get_current_user_id
from app.schemas.schedule import ScheduleBlockCreate, ScheduleBlockUpdate, ScheduleBlockResponse
from app.services.schedule import ScheduleService


router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@router.get("/blocks", response_model=list[ScheduleBlockResponse])
async def get_schedule_blocks(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Get all schedule blocks for current user."""
    service = ScheduleService(session)
    return await service.get_blocks(user_id)


@router.post("/blocks", response_model=ScheduleBlockResponse)
async def create_schedule_block(
    payload: ScheduleBlockCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Create a new schedule block."""
    service = ScheduleService(session)
    return await service.create_block(user_id, payload)


@router.put("/blocks/{block_id}", response_model=ScheduleBlockResponse)
async def update_schedule_block(
    block_id: int,
    payload: ScheduleBlockUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Update a schedule block."""
    service = ScheduleService(session)
    try:
        return await service.update_block(block_id, user_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/blocks/{block_id}")
async def delete_schedule_block(
    block_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Delete a schedule block."""
    service = ScheduleService(session)
    try:
        await service.delete_block(block_id, user_id)
        return {"message": "Schedule block deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ics")
async def export_schedule_ics(
    timezone: str | None = Query(default=None, description="Override timezone"),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Export schedule blocks as an ICS calendar file."""
    service = ScheduleService(session)
    ics_content = await service.export_ics(user_id, timezone_override=timezone)
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": 'attachment; filename="finance-schedule.ics"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/ics/public/{token}")
async def export_public_schedule_ics(
    token: str,
    timezone: str | None = Query(default=None, description="Override timezone"),
    session: AsyncSession = Depends(get_db),
):
    """Export schedule blocks as a public ICS calendar feed."""
    service = ScheduleService(session)
    ics_content = await service.export_ics_by_token(token, timezone_override=timezone)
    if not ics_content:
        raise HTTPException(status_code=404, detail="Calendar feed not found")
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": 'inline; filename="finance-schedule.ics"',
            "Cache-Control": "no-store",
        },
    )
