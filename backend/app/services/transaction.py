"""Transaction service for transaction-related business logic."""
import csv
import hashlib
import re
import unicodedata
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

        csv_reader = self._get_csv_reader(csv_content)
        imported = 0
        skipped = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Map CSV columns to transaction fields
                transaction_data = {}
                tags = []
                notes = []
                category_name = None
                debit_amount = None
                credit_amount = None
                transaction_type = None
                
                for csv_col, field_name in column_mapping.items():
                    if csv_col in row and row[csv_col]:
                        value = str(row[csv_col]).strip()
                        if field_name == "transaction_date":
                            transaction_data[field_name] = self._parse_date(value)
                        elif field_name == "amount":
                            transaction_data[field_name] = self._parse_amount(value)
                        elif field_name == "debit_amount":
                            debit_amount = self._parse_amount(value)
                        elif field_name == "credit_amount":
                            credit_amount = self._parse_amount(value)
                        elif field_name == "transaction_type":
                            transaction_type = value.lower()
                        elif field_name == "category_name":
                            category_name = value
                        elif field_name == "tags":
                            tags.append(value)
                        elif field_name == "notes":
                            notes.append(value)
                        else:
                            transaction_data[field_name] = value

                if "amount" not in transaction_data:
                    if debit_amount is not None and (credit_amount is None or credit_amount == 0):
                        transaction_data["amount"] = -abs(debit_amount)
                    elif credit_amount is not None and (debit_amount is None or debit_amount == 0):
                        transaction_data["amount"] = abs(credit_amount)
                    elif debit_amount is not None and credit_amount is not None:
                        transaction_data["amount"] = abs(credit_amount) - abs(debit_amount)

                # Normalize amount based on transaction type if provided
                if transaction_type and "amount" in transaction_data:
                    if transaction_type in {"debit", "expense", "outflow"}:
                        transaction_data["amount"] = -abs(Decimal(str(transaction_data["amount"])))
                    elif transaction_type in {"credit", "income", "inflow"}:
                        transaction_data["amount"] = abs(Decimal(str(transaction_data["amount"])))

                if tags:
                    transaction_data["tags"] = ", ".join([t for t in tags if t])
                if notes:
                    transaction_data["notes"] = " | ".join([n for n in notes if n])

                if not transaction_data.get("description"):
                    transaction_data["description"] = category_name or "Imported transaction"

                if category_name and transaction_data.get("amount") is not None:
                    is_income = Decimal(str(transaction_data["amount"])) > 0
                    category_id = await self._resolve_category_id(user_id, category_name, is_income)
                    transaction_data["category_id"] = category_id
                
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

    async def analyze_csv(
        self,
        csv_content: str,
        column_mapping: dict[str, str],
    ) -> dict:
        """Analyze CSV to compute earnings vs expenses before import."""
        csv_reader = self._get_csv_reader(csv_content)
        income_total = Decimal("0")
        expense_total = Decimal("0")
        rows = 0
        errors = 0
        income_sources: dict[str, dict] = {}
        expense_sources: dict[str, dict] = {}

        for row in csv_reader:
            rows += 1
            try:
                transaction_data = {}
                debit_amount = None
                credit_amount = None
                transaction_type = None
                description = None
                for csv_col, field_name in column_mapping.items():
                    if csv_col in row and row[csv_col]:
                        value = str(row[csv_col]).strip()
                        if field_name == "transaction_date":
                            transaction_data[field_name] = self._parse_date(value)
                        elif field_name == "amount":
                            transaction_data[field_name] = self._parse_amount(value)
                        elif field_name == "debit_amount":
                            debit_amount = self._parse_amount(value)
                        elif field_name == "credit_amount":
                            credit_amount = self._parse_amount(value)
                        elif field_name == "transaction_type":
                            transaction_type = value.lower()
                        elif field_name == "description":
                            description = value
                        else:
                            transaction_data[field_name] = value

                if "amount" not in transaction_data:
                    if debit_amount is not None and (credit_amount is None or credit_amount == 0):
                        transaction_data["amount"] = -abs(debit_amount)
                    elif credit_amount is not None and (debit_amount is None or debit_amount == 0):
                        transaction_data["amount"] = abs(credit_amount)
                    elif debit_amount is not None and credit_amount is not None:
                        transaction_data["amount"] = abs(credit_amount) - abs(debit_amount)

                if transaction_type and "amount" in transaction_data:
                    if transaction_type in {"debit", "expense", "outflow"}:
                        transaction_data["amount"] = -abs(Decimal(str(transaction_data["amount"])))
                    elif transaction_type in {"credit", "income", "inflow"}:
                        transaction_data["amount"] = abs(Decimal(str(transaction_data["amount"])))

                amount = transaction_data.get("amount")
                if amount is None:
                    errors += 1
                    continue
                amount_value = Decimal(str(amount))
                label = description or transaction_data.get("description") or "Unlabeled"
                if amount_value >= 0:
                    income_total += amount_value
                    entry = income_sources.setdefault(label, {"amount": Decimal("0"), "count": 0})
                    entry["amount"] += amount_value
                    entry["count"] += 1
                else:
                    expense_total += abs(amount_value)
                    entry = expense_sources.setdefault(label, {"amount": Decimal("0"), "count": 0})
                    entry["amount"] += abs(amount_value)
                    entry["count"] += 1
            except Exception:
                errors += 1

        def build_top(items: dict[str, dict]) -> list[dict]:
            sorted_items = sorted(
                items.items(),
                key=lambda item: item[1]["amount"],
                reverse=True,
            )
            return [
                {
                    "name": label,
                    "amount": float(data["amount"]),
                    "count": data["count"],
                }
                for label, data in sorted_items[:5]
            ]

        return {
            "rows": rows,
            "errors": errors,
            "income_total": float(income_total),
            "expense_total": float(expense_total),
            "net_total": float(income_total - expense_total),
            "top_income_sources": build_top(income_sources),
            "top_expense_sources": build_top(expense_sources),
        }

    def detect_column_mapping(self, csv_content: str) -> tuple[dict[str, str], list[str]]:
        """Detect CSV headers and build a best-effort column mapping."""
        reader = self._get_csv_reader(csv_content)
        headers = reader.fieldnames or []
        if not headers:
            raise ValueError("CSV file is missing a header row.")
        mapping = self._build_column_mapping(headers)
        unmapped = [header for header in headers if header not in mapping]
        return mapping, unmapped

    def _get_csv_reader(self, csv_content: str) -> csv.DictReader:
        sample = csv_content[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        return csv.DictReader(StringIO(csv_content), dialect=dialect, skipinitialspace=True)

    def _build_column_mapping(self, headers: list[str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        chosen_fields = set()

        date_headers = {
            "date",
            "transactiondate",
            "bookingdate",
            "posteddate",
            "valuedate",
            "datedoperation",
            "operationdate",
        }
        amount_headers = {
            "amount",
            "montant",
            "montantusd",
            "montantcad",
            "montanteur",
            "amountusd",
            "amountcad",
            "amountbase",
            "value",
            "valeur",
            "netamount",
            "total",
        }
        debit_headers = {
            "debit",
            "debitamount",
            "withdrawal",
            "sortie",
            "debitusd",
            "debitcad",
        }
        credit_headers = {
            "credit",
            "creditamount",
            "deposit",
            "entree",
            "creditusd",
            "creditcad",
        }
        description_headers = {
            "description",
            "details",
            "detail",
            "memo",
            "libelle",
            "label",
            "merchant",
            "merchantname",
            "payee",
            "beneficiaire",
            "entreprise",
            "company",
            "name",
        }
        category_headers = {
            "category",
            "categorie",
            "categoryname",
            "categoriename",
            "categorieoperation",
        }
        tag_headers = {
            "tags",
            "tag",
            "labels",
            "label",
            "etiquette",
            "etiquettes",
            "lieu",
            "location",
            "city",
            "ville",
        }
        notes_headers = {
            "notes",
            "note",
            "comment",
            "commentaire",
            "remarks",
            "reference",
        }
        type_headers = {
            "type",
            "transactiontype",
            "movement",
            "sens",
            "direction",
            "debitcredit",
            "drcr",
        }
        currency_headers = {
            "currency",
            "devise",
            "monnaie",
            "ccy",
        }

        for header in headers:
            normalized = self._normalize_header(header)
            if normalized in date_headers and "transaction_date" not in chosen_fields:
                mapping[header] = "transaction_date"
                chosen_fields.add("transaction_date")
            elif normalized in amount_headers and "amount" not in chosen_fields:
                mapping[header] = "amount"
                chosen_fields.add("amount")
            elif normalized in debit_headers:
                mapping[header] = "debit_amount"
            elif normalized in credit_headers:
                mapping[header] = "credit_amount"
            elif normalized in type_headers and "transaction_type" not in chosen_fields:
                mapping[header] = "transaction_type"
                chosen_fields.add("transaction_type")
            elif normalized in description_headers and "description" not in chosen_fields:
                mapping[header] = "description"
                chosen_fields.add("description")
            elif normalized in category_headers and "category_name" not in chosen_fields:
                mapping[header] = "category_name"
                chosen_fields.add("category_name")
            elif normalized in tag_headers:
                mapping[header] = "tags"
            elif normalized in notes_headers:
                mapping[header] = "notes"
            elif normalized in currency_headers and "currency" not in chosen_fields:
                mapping[header] = "currency"
                chosen_fields.add("currency")

        return mapping

    def _normalize_header(self, header: str) -> str:
        normalized = unicodedata.normalize("NFKD", header)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = normalized.lower()
        return re.sub(r"[^a-z0-9]+", "", normalized)

    async def _resolve_category_id(self, user_id: int, name: str, is_income: bool) -> int | None:
        if not name:
            return None
        existing = await self.category_service.repository.get_by_name(user_id, name)
        if existing:
            return existing.id
        created = await self.category_service.create_category(
            user_id=user_id,
            name=name,
            is_income=is_income,
        )
        return created.id

    def _parse_date(self, raw_value: str) -> datetime:
        value = raw_value.strip()
        if not value:
            raise ValueError("Empty date value")
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unsupported date format: {raw_value}")

    def _parse_amount(self, raw_value: str) -> Decimal:
        """Parse a numeric amount from CSV, handling signs and separators."""
        value = raw_value.strip()
        negative = False
        if value.startswith("(") and value.endswith(")"):
            negative = True
            value = value[1:-1]
        value = re.sub(r"[\s\u00A0]", "", value)
        value = value.replace("$", "").replace("€", "").replace("£", "")
        value = re.sub(r"[^0-9,.\-+]", "", value)
        if value.startswith("-"):
            negative = True
            value = value[1:]
        if value.startswith("+"):
            value = value[1:]
        if not value:
            raise ValueError("Empty amount")

        decimal_sep = None
        if "." in value or "," in value:
            last_dot = value.rfind(".")
            last_comma = value.rfind(",")
            if last_dot == -1:
                decimal_sep = ","
            elif last_comma == -1:
                decimal_sep = "."
            else:
                decimal_sep = "." if last_dot > last_comma else ","

            if decimal_sep:
                parts = value.split(decimal_sep)
                if len(parts) >= 2 and len(parts[-1]) == 3 and all(len(p) == 3 for p in parts[1:]):
                    decimal_sep = None

        if decimal_sep:
            parts = value.split(decimal_sep)
            integer_part = re.sub(r"[.,]", "", parts[0])
            fraction_part = "".join(parts[1:])
            normalized = f"{integer_part}.{fraction_part}" if fraction_part else integer_part
        else:
            normalized = re.sub(r"[.,]", "", value)

        if not normalized:
            raise ValueError("Invalid amount")
        amount = Decimal(normalized)
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
