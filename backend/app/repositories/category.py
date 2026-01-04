"""Category repository for database operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.category import Category, CategoryRule


class CategoryRepository:
    """Repository for category operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, category_id: int, user_id: int) -> Category | None:
        """Get category by ID (ensure user ownership)."""
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_user(self, user_id: int) -> list[Category]:
        """Get all categories for user."""
        result = await self.session.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.created_at)
        )
        return list(result.scalars().all())

    async def get_by_name(self, user_id: int, name: str) -> Category | None:
        """Get category by name (case-insensitive)."""
        result = await self.session.execute(
            select(Category).where(
                Category.user_id == user_id,
                func.lower(Category.name) == name.lower(),
            )
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_id: int, **kwargs) -> Category:
        """Create a new category."""
        category = Category(user_id=user_id, **kwargs)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def update(self, category_id: int, user_id: int, **kwargs) -> Category | None:
        """Update category."""
        category = await self.get_by_id(category_id, user_id)
        if not category:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(category, key, value)
        
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def delete(self, category_id: int, user_id: int) -> bool:
        """Delete category."""
        category = await self.get_by_id(category_id, user_id)
        if not category:
            return False
        
        await self.session.delete(category)
        await self.session.commit()
        return True


class CategoryRuleRepository:
    """Repository for category rule operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, rule_id: int, category_id: int) -> CategoryRule | None:
        """Get rule by ID."""
        result = await self.session.execute(
            select(CategoryRule).where(
                CategoryRule.id == rule_id,
                CategoryRule.category_id == category_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_category(self, category_id: int) -> list[CategoryRule]:
        """Get all rules for a category."""
        result = await self.session.execute(
            select(CategoryRule)
            .where(CategoryRule.category_id == category_id, CategoryRule.is_active)
            .order_by(CategoryRule.priority.desc())
        )
        return list(result.scalars().all())
    
    async def create(self, category_id: int, **kwargs) -> CategoryRule:
        """Create a new rule."""
        rule = CategoryRule(category_id=category_id, **kwargs)
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule
    
    async def update(self, rule_id: int, category_id: int, **kwargs) -> CategoryRule | None:
        """Update rule."""
        rule = await self.get_by_id(rule_id, category_id)
        if not rule:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(rule, key, value)
        
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule
    
    async def delete(self, rule_id: int, category_id: int) -> bool:
        """Delete rule."""
        rule = await self.get_by_id(rule_id, category_id)
        if not rule:
            return False
        
        await self.session.delete(rule)
        await self.session.commit()
        return True
