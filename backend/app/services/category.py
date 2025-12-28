"""Category service for category-related business logic."""
import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.category import CategoryRepository, CategoryRuleRepository
from app.models.category import RuleType
from app.schemas.category import CategoryResponse, CategoryRuleResponse


class CategoryService:
    """Service for category operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = CategoryRepository(session)
        self.rule_repository = CategoryRuleRepository(session)
        self.session = session
    
    async def get_category(self, category_id: int, user_id: int) -> CategoryResponse:
        """Get category by ID."""
        category = await self.repository.get_by_id(category_id, user_id)
        if not category:
            raise ValueError("Category not found")
        return CategoryResponse.from_orm(category)
    
    async def get_all_categories(self, user_id: int) -> list[CategoryResponse]:
        """Get all categories for user."""
        categories = await self.repository.get_all_by_user(user_id)
        return [CategoryResponse.from_orm(cat) for cat in categories]
    
    async def create_category(self, user_id: int, **kwargs) -> CategoryResponse:
        """Create a new category."""
        category = await self.repository.create(user_id=user_id, **kwargs)
        return CategoryResponse.from_orm(category)
    
    async def update_category(self, category_id: int, user_id: int, **kwargs) -> CategoryResponse:
        """Update category."""
        category = await self.repository.update(category_id, user_id, **kwargs)
        if not category:
            raise ValueError("Category not found")
        return CategoryResponse.from_orm(category)
    
    async def delete_category(self, category_id: int, user_id: int) -> bool:
        """Delete category."""
        success = await self.repository.delete(category_id, user_id)
        if not success:
            raise ValueError("Category not found")
        return success
    
    async def apply_rules(self, description: str, user_id: int) -> int | None:
        """Apply categorization rules to auto-categorize a transaction."""
        categories = await self.repository.get_all_by_user(user_id)
        
        for category in categories:
            rules = await self.rule_repository.get_all_by_category(category.id)
            
            for rule in rules:
                if self._matches_rule(description, rule.rule_type, rule.pattern):
                    return category.id
        
        return None
    
    def _matches_rule(self, text: str, rule_type: str, pattern: str) -> bool:
        """Check if text matches a rule."""
        text_lower = text.lower()
        
        if rule_type == RuleType.CONTAINS:
            return pattern.lower() in text_lower
        elif rule_type == RuleType.EXACT_MATCH:
            return pattern.lower() == text_lower
        elif rule_type == RuleType.REGEX:
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except re.error:
                return False
        
        return False


class CategoryRuleService:
    """Service for category rule operations."""
    
    def __init__(self, session: AsyncSession):
        self.repository = CategoryRuleRepository(session)
        self.session = session
    
    async def get_rule(self, rule_id: int, category_id: int) -> CategoryRuleResponse:
        """Get rule by ID."""
        rule = await self.repository.get_by_id(rule_id, category_id)
        if not rule:
            raise ValueError("Rule not found")
        return CategoryRuleResponse.from_orm(rule)
    
    async def get_all_rules(self, category_id: int) -> list[CategoryRuleResponse]:
        """Get all rules for a category."""
        rules = await self.repository.get_all_by_category(category_id)
        return [CategoryRuleResponse.from_orm(rule) for rule in rules]
    
    async def create_rule(self, category_id: int, **kwargs) -> CategoryRuleResponse:
        """Create a new rule."""
        rule = await self.repository.create(category_id=category_id, **kwargs)
        return CategoryRuleResponse.from_orm(rule)
    
    async def update_rule(self, rule_id: int, category_id: int, **kwargs) -> CategoryRuleResponse:
        """Update rule."""
        rule = await self.repository.update(rule_id, category_id, **kwargs)
        if not rule:
            raise ValueError("Rule not found")
        return CategoryRuleResponse.from_orm(rule)
    
    async def delete_rule(self, rule_id: int, category_id: int) -> bool:
        """Delete rule."""
        success = await self.repository.delete(rule_id, category_id)
        if not success:
            raise ValueError("Rule not found")
        return success
