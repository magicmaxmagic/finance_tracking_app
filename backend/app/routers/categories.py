"""Category router for category management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CategoryRuleCreate, CategoryRuleResponse
)
from app.services.category import CategoryService, CategoryRuleService
from app.core.deps import get_current_user_id

router = APIRouter(prefix="/api/categories", tags=["categories"])


# Category endpoints
@router.get("", response_model=list[CategoryResponse])
async def get_categories(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get all categories for current user."""
    service = CategoryService(session)
    return await service.get_all_categories(user_id)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get category by ID."""
    service = CategoryService(session)
    try:
        return await service.get_category(category_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Create a new category."""
    service = CategoryService(session)
    try:
        return await service.create_category(user_id, **category_data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Update category."""
    service = CategoryService(session)
    try:
        update_data = category_data.dict(exclude_unset=True)
        return await service.update_category(category_id, user_id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete category."""
    service = CategoryService(session)
    try:
        await service.delete_category(category_id, user_id)
        return {"message": "Category deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Category rule endpoints
@router.get("/{category_id}/rules", response_model=list[CategoryRuleResponse])
async def get_category_rules(
    category_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Get all rules for a category."""
    category_service = CategoryService(session)
    
    # Verify category ownership
    try:
        await category_service.get_category(category_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")
    
    rule_service = CategoryRuleService(session)
    return await rule_service.get_all_rules(category_id)


@router.post("/{category_id}/rules", response_model=CategoryRuleResponse)
async def create_category_rule(
    category_id: int,
    rule_data: CategoryRuleCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Create a category rule."""
    category_service = CategoryService(session)
    
    # Verify category ownership
    try:
        await category_service.get_category(category_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")
    
    rule_service = CategoryRuleService(session)
    try:
        return await rule_service.create_rule(category_id, **rule_data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{category_id}/rules/{rule_id}", response_model=CategoryRuleResponse)
async def update_category_rule(
    category_id: int,
    rule_id: int,
    rule_data: CategoryRuleCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Update a category rule."""
    category_service = CategoryService(session)
    
    # Verify category ownership
    try:
        await category_service.get_category(category_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")
    
    rule_service = CategoryRuleService(session)
    try:
        update_data = rule_data.dict(exclude_unset=True)
        return await rule_service.update_rule(rule_id, category_id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}/rules/{rule_id}")
async def delete_category_rule(
    category_id: int,
    rule_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db)
):
    """Delete a category rule."""
    category_service = CategoryService(session)
    
    # Verify category ownership
    try:
        await category_service.get_category(category_id, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Category not found")
    
    rule_service = CategoryRuleService(session)
    try:
        await rule_service.delete_rule(rule_id, category_id)
        return {"message": "Rule deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
