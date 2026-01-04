"""Import transactions from CSV into the database."""
import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.core.config import settings
from app.core.security import hash_password


def get_session() -> Session:
    """Create database session."""
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def import_csv(csv_path: str = "test.csv"):
    """Import transactions from CSV file."""
    session = get_session()
    
    try:
        # 1. Create test user
        print("📝 Creating test user...")
        user = session.query(User).filter(User.email == "test@example.com").first()
        
        if not user:
            user = User(
                email="test@example.com",
                hashed_password=hash_password("password123"),
                full_name="Test User",
                is_active=True,
                is_email_verified=True,
            )
            session.add(user)
            session.commit()
            print(f"✅ Created user: {user.email} (ID: {user.id})")
        else:
            print(f"✅ User already exists: {user.email} (ID: {user.id})")

        # 2. Create account for user
        print("\n📝 Creating account...")
        account = session.query(Account).filter(
            Account.user_id == user.id,
            Account.name == "Chequings Account"
        ).first()
        
        if not account:
            account = Account(
                user_id=user.id,
                name="Chequings Account",
                account_type="checking",
                currency="USD",
                balance=Decimal("0.00"),
                is_active=True,
            )
            session.add(account)
            session.commit()
            print(f"✅ Created account: {account.name} (ID: {account.id})")
        else:
            print(f"✅ Account already exists: {account.name} (ID: {account.id})")

        # 3. Create categories
        print("\n📝 Creating categories...")
        categories_to_create = {
            "Income": "income",
            "Rent": "expense",
            "Groceries": "expense",
            "Subscriptions": "expense",
            "Freelance": "income",
            "Restaurants": "expense",
            "Transportation": "expense",
            "Utilities": "expense",
            "Clothing": "expense",
            "Gas": "expense",
        }
        
        categories = {}
        for cat_name, cat_type in categories_to_create.items():
            cat = session.query(Category).filter(
                Category.user_id == user.id,
                Category.name == cat_name
            ).first()
            
            if not cat:
                cat = Category(
                    user_id=user.id,
                    name=cat_name,
                    is_income=cat_type == "income",
                )
                session.add(cat)
                session.commit()
                print(f"  ✅ Created category: {cat_name}")
            else:
                print(f"  ✅ Category exists: {cat_name}")
            
            categories[cat_name] = cat

        # 4. Import transactions from CSV
        print(f"\n📊 Importing transactions from {csv_path}...")
        
        csv_full_path = Path(__file__).parent.parent.parent / csv_path
        
        if not csv_full_path.exists():
            print(f"❌ CSV file not found: {csv_full_path}")
            return
        
        # Mapping of company to category
        company_to_category = {
            "Employer": "Income",
            "Freelance Client": "Freelance",
            "SaaS Client": "Freelance",
            "Landlord": "Rent",
            "IGA": "Groceries",
            "Spotify": "Subscriptions",
            "Netflix": "Subscriptions",
            "STM": "Transportation",
            "Restaurant": "Restaurants",
            "Bell Internet": "Utilities",
            "Uber Eats": "Restaurants",
            "Shell Gas": "Gas",
            "Uniqlo": "Clothing",
        }
        
        imported_count = 0
        skipped_count = 0
        
        with open(csv_full_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    amount = Decimal(row['amount_usd'])
                    location = row['location']
                    company = row['company']
                    
                    # Determine category
                    category_name = company_to_category.get(company, "Income" if amount > 0 else "Groceries")
                    category = categories.get(category_name)
                    
                    if not category:
                        print(f"  ⚠️  Category not found for {company}, skipping")
                        skipped_count += 1
                        continue
                    
                    # Check if transaction already exists
                    existing = session.query(Transaction).filter(
                        Transaction.user_id == user.id,
                        Transaction.account_id == account.id,
                        Transaction.transaction_date == date,
                        Transaction.amount == amount,
                        Transaction.description == company,
                    ).first()
                    
                    if not existing:
                        transaction = Transaction(
                            user_id=user.id,
                            account_id=account.id,
                            category_id=category.id,
                            amount=amount,
                            description=f"{company} - {location}",
                            transaction_date=date,
                        )
                        session.add(transaction)
                        imported_count += 1
                    else:
                        skipped_count += 1
                
                except Exception as e:
                    print(f"  ❌ Error importing row {row}: {e}")
                    skipped_count += 1
        
        # Commit all transactions
        session.commit()
        print(f"\n✅ Imported {imported_count} transactions")
        print(f"⏭️  Skipped {skipped_count} duplicate transactions")
        print(f"\n🎉 CSV import complete!")

    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "test.csv"
    import_csv(csv_file)
