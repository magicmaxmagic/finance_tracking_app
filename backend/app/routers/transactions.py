"""Transaction router for transaction management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionListResponse
)
from app.services.transaction import TransactionService
from app.core.deps import get_current_user_id
from datetime import datetime

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _decode_csv(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


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
        csv_content = _decode_csv(content)
        column_mapping, unmapped = service.detect_column_mapping(csv_content)

        has_amount = any(
            field in {"amount", "debit_amount", "credit_amount"} for field in column_mapping.values()
        )
        has_date = "transaction_date" in column_mapping.values()
        if not has_amount or not has_date:
            raise ValueError(
                "CSV columns not recognized. "
                "Ensure you have date and amount columns (e.g., Date, Amount, Debit/Credit)."
            )
        
        from app.services.job import JobService
        job_service = JobService(session)
        job = await job_service.create_job(
            user_id=user_id,
            job_type="csv_import",
            payload={
                "account_id": account_id,
                "skip_duplicates": skip_duplicates,
                "unmapped_columns": unmapped,
            },
        )
        asyncio.create_task(
            TransactionService.run_csv_import_job(
                job.id,
                user_id,
                account_id,
                csv_content,
                column_mapping,
                skip_duplicates,
            )
        )
        return {"job_id": job.id, "status": "queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing CSV file")


@router.post("/import/preview")
async def preview_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    """Analyze CSV to preview expenses vs earnings."""
    service = TransactionService(session)
    try:
        content = await file.read()
        csv_content = _decode_csv(content)
        column_mapping, unmapped = service.detect_column_mapping(csv_content)
        has_amount = any(
            field in {"amount", "debit_amount", "credit_amount"} for field in column_mapping.values()
        )
        warnings = []
        if not has_amount:
            warnings.append("No amount column detected.")
        if "transaction_date" not in column_mapping.values():
            warnings.append("No date column detected.")

        analysis = await service.analyze_csv(csv_content, column_mapping)
        analysis["unmapped_columns"] = unmapped
        analysis["detected_fields"] = sorted(set(column_mapping.values()))
        analysis["warnings"] = warnings
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error processing CSV file")
