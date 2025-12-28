"""Account router for account management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.services.account import AccountService
from app.core.security import decode_token
from fastapi import Header

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract user ID from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization[7:]
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return int(user_id)


@router.get("", response_model=list[AccountResponse])
async def get_accounts(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get all accounts for current user."""
    service = AccountService(session)
    return await service.get_all_accounts(user_id)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get account by ID."""
    service = AccountService(session)
    try:
        return await service.get_account(account_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Create a new account."""
    service = AccountService(session)
    try:
        return await service.create_account(user_id, **account_data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Update account."""
    service = AccountService(session)
    try:
        update_data = account_data.dict(exclude_unset=True)
        return await service.update_account(account_id, user_id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete account."""
    service = AccountService(session)
    try:
        await service.delete_account(account_id, user_id)
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
