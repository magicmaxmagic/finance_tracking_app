"""Data export/import router."""
import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.base import get_db
from app.core.deps import get_current_user_id
from app.models.account import Account
from app.models.category import Category, CategoryRule
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.net_worth_snapshot import NetWorthSnapshot

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/export/transactions.csv")
async def export_transactions_csv(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Export transactions as CSV."""
    result = await session.execute(
        select(Transaction).where(Transaction.user_id == user_id)
    )
    transactions = result.scalars().all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "account_id", "category_id", "description", "amount", "currency",
        "transaction_date", "tags", "notes", "created_at",
    ])
    for tx in transactions:
        writer.writerow([
            tx.id,
            tx.account_id,
            tx.category_id,
            tx.description,
            str(tx.amount),
            tx.currency,
            tx.transaction_date.isoformat(),
            tx.tags,
            tx.notes,
            tx.created_at.isoformat(),
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/export/transactions.json")
async def export_transactions_json(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Export transactions as JSON."""
    result = await session.execute(
        select(Transaction).where(Transaction.user_id == user_id)
    )
    transactions = result.scalars().all()
    return [
        {
            "id": tx.id,
            "account_id": tx.account_id,
            "category_id": tx.category_id,
            "description": tx.description,
            "amount": str(tx.amount),
            "currency": tx.currency,
            "transaction_date": tx.transaction_date.isoformat(),
            "tags": tx.tags,
            "notes": tx.notes,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in transactions
    ]


@router.get("/backup")
async def backup_data(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Export user data for backup."""
    accounts = (await session.execute(select(Account).where(Account.user_id == user_id))).scalars().all()
    categories = (await session.execute(select(Category).where(Category.user_id == user_id))).scalars().all()
    rules = (await session.execute(
        select(CategoryRule).join(Category).where(Category.user_id == user_id)
    )).scalars().all()
    budgets = (await session.execute(select(Budget).where(Budget.user_id == user_id))).scalars().all()
    transactions = (await session.execute(select(Transaction).where(Transaction.user_id == user_id))).scalars().all()
    snapshots = (await session.execute(select(NetWorthSnapshot).where(NetWorthSnapshot.user_id == user_id))).scalars().all()

    return {
        "accounts": [
            {
                "id": acc.id,
                "name": acc.name,
                "account_type": acc.account_type,
                "balance": str(acc.balance),
                "currency": acc.currency,
            }
            for acc in accounts
        ],
        "categories": [
            {"id": cat.id, "name": cat.name, "color": cat.color, "icon": cat.icon, "is_income": cat.is_income, "description": cat.description}
            for cat in categories
        ],
        "category_rules": [
            {"category_id": rule.category_id, "rule_type": rule.rule_type, "pattern": rule.pattern, "priority": rule.priority}
            for rule in rules
        ],
        "budgets": [
            {"category_id": b.category_id, "amount": str(b.amount), "month": b.month.isoformat()}
            for b in budgets
        ],
        "transactions": [
            {
                "account_id": tx.account_id,
                "category_id": tx.category_id,
                "description": tx.description,
                "amount": str(tx.amount),
                "currency": tx.currency,
                "transaction_date": tx.transaction_date.isoformat(),
                "tags": tx.tags,
                "notes": tx.notes,
            }
            for tx in transactions
        ],
        "net_worth_snapshots": [
            {"month": snap.month.isoformat(), "total": str(snap.total)}
            for snap in snapshots
        ],
    }


@router.post("/restore")
async def restore_data(
    payload: dict,
    overwrite: bool = Query(False),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Restore user data from backup payload."""
    if not overwrite:
        raise HTTPException(status_code=400, detail="Set overwrite=true to restore data.")

    await session.execute(delete(Transaction).where(Transaction.user_id == user_id))
    await session.execute(delete(Budget).where(Budget.user_id == user_id))
    category_ids = [
        row[0]
        for row in (await session.execute(
            select(Category.id).where(Category.user_id == user_id)
        )).all()
    ]
    if category_ids:
        await session.execute(delete(CategoryRule).where(CategoryRule.category_id.in_(category_ids)))
    await session.execute(delete(Category).where(Category.user_id == user_id))
    await session.execute(delete(Account).where(Account.user_id == user_id))
    await session.execute(delete(NetWorthSnapshot).where(NetWorthSnapshot.user_id == user_id))
    await session.commit()

    for acc in payload.get("accounts", []):
        session.add(Account(user_id=user_id, **acc))
    await session.commit()

    for cat in payload.get("categories", []):
        session.add(Category(user_id=user_id, **cat))
    await session.commit()

    for rule in payload.get("category_rules", []):
        session.add(CategoryRule(**rule))
    await session.commit()

    from datetime import date, datetime

    for budget in payload.get("budgets", []):
        budget_data = budget.copy()
        if "month" in budget_data:
            budget_data["month"] = date.fromisoformat(budget_data["month"])
        session.add(Budget(user_id=user_id, **budget_data))
    await session.commit()

    for tx in payload.get("transactions", []):
        tx_data = tx.copy()
        if "transaction_date" in tx_data:
            tx_data["transaction_date"] = datetime.fromisoformat(tx_data["transaction_date"])
        session.add(Transaction(user_id=user_id, **tx_data))
    await session.commit()

    for snap in payload.get("net_worth_snapshots", []):
        snap_data = snap.copy()
        if "month" in snap_data:
            snap_data["month"] = date.fromisoformat(snap_data["month"])
        session.add(NetWorthSnapshot(user_id=user_id, **snap_data))
    await session.commit()

    return {"message": "Restore completed."}
