"""Transaction service for transaction-related business logic."""
import csv
import hashlib
from io import StringIO
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.transaction import TransactionRepository
from app.repositories.account import AccountRepository
from app.services.category import CategoryService
from app.schemas.transaction import TransactionResponse, TransactionListResponse
from app.db.base import AsyncSessionLocal
from app.services.job import JobService
from app.repositories.budget import BudgetRepository
from app.services.notification import NotificationService
from sqlalchemy import select, func, extract
from app.models.transaction import Transaction as TransactionModel
from decimal import Decimal


class TransactionService:
    """Service for transaction operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = TransactionRepository(session)
        self.account_repository = AccountRepository(session)
        self.category_service = CategoryService(session)
        self.budget_repository = BudgetRepository(session)
        self.notification_service = NotificationService(session)
        self.session = session
    
    async def get_transaction(self, transaction_id: int, user_id: int) -> TransactionResponse:
        """Get transaction by ID."""
        transaction = await self.repository.get_by_id(transaction_id, user_id)
        if not transaction:
            raise ValueError("Transaction not found")
        return TransactionResponse.from_orm(transaction)
    
    async def get_paginated_transactions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        category_id: int | None = None,
        account_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        search: str | None = None,
    ) -> TransactionListResponse:
        """Get paginated transactions with filters."""
        transactions, total = await self.repository.get_all_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            category_id=category_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )
        
        items = [TransactionResponse.from_orm(t) for t in transactions]
        total_pages = (total + limit - 1) // limit
        
        return TransactionListResponse(
            items=items,
            total=total,
            page=(skip // limit) + 1,
            page_size=limit,
            total_pages=total_pages,
        )
    
    async def create_transaction(self, user_id: int, **kwargs) -> TransactionResponse:
        """Create a new transaction."""
        # Auto-categorize if no category provided
        if not kwargs.get("category_id"):
            category_id = await self.category_service.apply_rules(
                kwargs.get("description", ""), user_id
            )
            if category_id:
                kwargs["category_id"] = category_id
        
        transaction = await self.repository.create(user_id=user_id, **kwargs)
        await self._notify_budget_thresholds(user_id, transaction)
        return TransactionResponse.from_orm(transaction)
    
    async def update_transaction(self, transaction_id: int, user_id: int, **kwargs) -> TransactionResponse:
        """Update transaction."""
        transaction = await self.repository.update(transaction_id, user_id, **kwargs)
        if not transaction:
            raise ValueError("Transaction not found")
        return TransactionResponse.from_orm(transaction)
    
    async def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Delete transaction."""
        success = await self.repository.delete(transaction_id, user_id)
        if not success:
            raise ValueError("Transaction not found")
        return success
    
    async def import_from_csv(
        self,
        user_id: int,
        account_id: int,
        csv_content: str,
        column_mapping: dict[str, str],
        skip_duplicates: bool = True,
    ) -> dict:
        """Import transactions from CSV."""
        # Verify account ownership
        account = await self.account_repository.get_by_id(account_id, user_id)
        if not account:
            raise ValueError("Account not found")
        
        csv_reader = csv.DictReader(StringIO(csv_content))
        imported = 0
        skipped = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Map CSV columns to transaction fields
                transaction_data = {}
                
                for csv_col, field_name in column_mapping.items():
                    if csv_col in row and row[csv_col]:
                        if field_name == "transaction_date":
                            transaction_data[field_name] = datetime.fromisoformat(row[csv_col])
                        elif field_name == "amount":
                            transaction_data[field_name] = self._parse_amount(row[csv_col])
                        elif field_name == "debit_amount":
                            debit_value = self._parse_amount(row[csv_col])
                            transaction_data["amount"] = -abs(debit_value)
                        elif field_name == "credit_amount":
                            credit_value = self._parse_amount(row[csv_col])
                            transaction_data["amount"] = abs(credit_value)
                        elif field_name == "transaction_type":
                            transaction_data[field_name] = row[csv_col].strip().lower()
                        else:
                            transaction_data[field_name] = row[csv_col]

                # Normalize amount based on transaction type if provided
                tx_type = transaction_data.pop("transaction_type", None)
                if tx_type and "amount" in transaction_data:
                    if tx_type in {"debit", "expense", "outflow"}:
                        transaction_data["amount"] = -abs(Decimal(str(transaction_data["amount"])))
                    elif tx_type in {"credit", "income", "inflow"}:
                        transaction_data["amount"] = abs(Decimal(str(transaction_data["amount"])))
                
                # Generate import ID for deduplication
                import_data = f"{account_id}_{transaction_data.get('transaction_date')}_{transaction_data.get('amount')}_{transaction_data.get('description')}"
                import_id = hashlib.md5(import_data.encode()).hexdigest()
                
                # Check if already imported
                existing = await self.repository.get_by_import_id(import_id, user_id)
                if existing:
                    if skip_duplicates:
                        skipped += 1
                        continue
                    else:
                        # Mark as duplicate
                        transaction_data["is_duplicate"] = True
                        transaction_data["duplicate_of_id"] = existing.id
                
                transaction_data["import_id"] = import_id
                transaction_data["account_id"] = account_id
                
                # Create transaction
                await self.create_transaction(user_id=user_id, **transaction_data)
                imported += 1
                
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }

    def _parse_amount(self, raw_value: str) -> Decimal:
        """Parse a numeric amount from CSV, handling signs and separators."""
        value = raw_value.strip()
        negative = False
        if value.startswith("(") and value.endswith(")"):
            negative = True
            value = value[1:-1]
        value = value.replace(",", "").replace(" ", "")
        value = value.replace("$", "").replace("€", "").replace("£", "")
        if value.startswith("-"):
            negative = True
            value = value[1:]
        if value.startswith("+"):
            value = value[1:]
        amount = Decimal(value)
        return -amount if negative else amount

    async def _notify_budget_thresholds(self, user_id: int, transaction) -> None:
        """Create notification when budget is exceeded."""
        if not transaction.category_id or float(transaction.amount) >= 0:
            return
        month = transaction.transaction_date.date().replace(day=1)
        budget = await self.budget_repository.get_by_category_and_month(
            user_id=user_id,
            category_id=transaction.category_id,
            month=month,
        )
        if not budget:
            return
        spent = await self._get_spent_amount(transaction.category_id, month.year, month.month)
        if spent > budget.amount:
            await self.notification_service.create_notification(
                user_id=user_id,
                title="Budget exceeded",
                message=f"The {budget.category.name} budget for {month.isoformat()} is exceeded.",
                notification_type="warning",
            )

    async def _get_spent_amount(self, category_id: int, year: int, month: int) -> Decimal:
        """Get total spent in a category for a month."""
        result = await self.session.execute(
            select(func.sum(TransactionModel.amount)).where(
                TransactionModel.category_id == category_id,
                extract('year', TransactionModel.transaction_date) == year,
                extract('month', TransactionModel.transaction_date) == month,
                TransactionModel.amount < 0,
            )
        )
        total = result.scalar() or 0
        return Decimal(str(abs(float(total))))

    @staticmethod
    async def run_csv_import_job(
        job_id: int,
        user_id: int,
        account_id: int,
        csv_content: str,
        column_mapping: dict[str, str],
        skip_duplicates: bool,
    ) -> None:
        """Run CSV import as a background job."""
        async with AsyncSessionLocal() as session:
            job_service = JobService(session)
            transaction_service = TransactionService(session)
            job = await job_service.get_job(job_id, user_id)
            if not job:
                return
            await job_service.update_status(job, "running")
            try:
                result = await transaction_service.import_from_csv(
                    user_id=user_id,
                    account_id=account_id,
                    csv_content=csv_content,
                    column_mapping=column_mapping,
                    skip_duplicates=skip_duplicates,
                )
                await job_service.update_status(job, "completed", result=result)
            except Exception as exc:
                await job_service.update_status(job, "failed", error=str(exc))
