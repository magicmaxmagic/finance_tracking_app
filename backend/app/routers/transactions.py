"""Transaction router for transaction management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionListResponse, CSVImportRequest
)
from app.services.transaction import TransactionService
from app.core.security import decode_token
from fastapi import Header
from datetime import datetime

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract user ID from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization[7:]
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    return int(user_id)


@router.get("", response_model=TransactionListResponse)
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    category_id: int | None = None,
    account_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get paginated transactions."""
    service = TransactionService(session)
    
    # Parse dates if provided
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
    
    try:
        return await service.get_paginated_transactions(
            user_id=user_id,
            skip=skip,
            limit=limit,
            category_id=category_id,
            account_id=account_id,
            start_date=start_dt,
            end_date=end_dt,
            search=search,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get transaction by ID."""
    service = TransactionService(session)
    try:
        return await service.get_transaction(transaction_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Create a new transaction."""
    service = TransactionService(session)
    try:
        return await service.create_transaction(user_id, **transaction_data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Update transaction."""
    service = TransactionService(session)
    try:
        update_data = transaction_data.dict(exclude_unset=True)
        return await service.update_transaction(transaction_id, user_id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete transaction."""
    service = TransactionService(session)
    try:
        await service.delete_transaction(transaction_id, user_id)
        return {"message": "Transaction deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import/csv")
async def import_csv(
    account_id: int,
    file: UploadFile = File(...),
    skip_duplicates: bool = True,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Import transactions from CSV file."""
    service = TransactionService(session)
    
    try:
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Simple mapping: try to detect standard column names
        column_mapping = {
            "Date": "transaction_date",
            "Amount": "amount",
            "Description": "description",
            "Category": "category_id",
        }
        
        result = await service.import_from_csv(
            user_id=user_id,
            account_id=account_id,
            csv_content=csv_content,
            column_mapping=column_mapping,
            skip_duplicates=skip_duplicates,
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing CSV file")
