"""
Companion CRUD API Routes
Frontend-compatible endpoints for AI character management
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from ...config.database import get_db
from ...models.companion import Companion, Category

router = APIRouter(prefix="/companions", tags=["companions"])


# ===== PYDANTIC SCHEMAS =====

class PersonalityTraits(BaseModel):
    """Personality trait scales (1-5)"""
    humor: int = Field(ge=1, le=5, default=3)
    empathy: int = Field(ge=1, le=5, default=3)
    assertiveness: int = Field(ge=1, le=5, default=3)
    sarcasm: int = Field(ge=1, le=5, default=3)


class ModerationSettings(BaseModel):
    """Content moderation settings (1-5)"""
    hate_moderation: int = Field(ge=1, le=5, default=3)
    harassment_moderation: int = Field(ge=1, le=5, default=3)
    violence_moderation: int = Field(ge=1, le=5, default=3)
    self_harm_moderation: int = Field(ge=1, le=5, default=3)
    sexual_moderation: int = Field(ge=1, le=5, default=3)


class CompanionCreate(BaseModel):
    """Schema for creating new companions"""
    name: str = Field(min_length=1, max_length=100)
    short_description: str = Field(min_length=1, max_length=500)
    character_description: dict = Field(default={})
    category_id: str
    src: str = Field(description="Avatar image URL")
    personality_traits: PersonalityTraits = Field(default_factory=PersonalityTraits)
    moderation_settings: ModerationSettings = Field(default_factory=ModerationSettings)


class CompanionUpdate(BaseModel):
    """Schema for updating companions"""
    name: Optional[str] = None
    short_description: Optional[str] = None
    character_description: Optional[dict] = None
    category_id: Optional[str] = None
    src: Optional[str] = None
    personality_traits: Optional[PersonalityTraits] = None
    moderation_settings: Optional[ModerationSettings] = None


class CompanionResponse(BaseModel):
    """Response schema for companion data"""
    id: str
    user_id: str
    user_name: str
    name: str
    short_description: str
    character_description: dict
    category_id: str
    src: str
    created_at: str
    updated_at: str
    
    # Personality traits
    humor: int
    empathy: int
    assertiveness: int
    sarcasm: int
    
    # Moderation settings
    hate_moderation: int
    harassment_moderation: int
    violence_moderation: int
    self_harm_moderation: int
    sexual_moderation: int
    
    @classmethod
    def from_db_model(cls, companion):
        """Create response from database model"""
        return cls(
            id=str(companion.id),
            user_id=companion.user_id,
            user_name=companion.user_name,
            name=companion.name,
            short_description=companion.short_description,
            character_description=companion.character_description,
            category_id=str(companion.category_id),
            src=companion.src,
            created_at=companion.created_at.isoformat(),
            updated_at=companion.updated_at.isoformat(),
            humor=companion.humor,
            empathy=companion.empathy,
            assertiveness=companion.assertiveness,
            sarcasm=companion.sarcasm,
            hate_moderation=companion.hate_moderation,
            harassment_moderation=companion.harassment_moderation,
            violence_moderation=companion.violence_moderation,
            self_harm_moderation=companion.self_harm_moderation,
            sexual_moderation=companion.sexual_moderation
        )


class CategoryResponse(BaseModel):
    """Response schema for categories"""
    id: str
    name: str
    
    @classmethod
    def from_db_model(cls, category):
        """Create response from database model"""
        return cls(
            id=str(category.id),
            name=category.name
        )


# ===== API ENDPOINTS =====

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all companion categories"""
    try:
        result = await db.execute(select(Category))
        categories = result.scalars().all()
        return [CategoryResponse.from_db_model(cat) for cat in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    name: str,
    db: AsyncSession = Depends(get_db)
):
    """Create a new category"""
    try:
        # Check if category already exists
        result = await db.execute(select(Category).where(Category.name == name))
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail="Category already exists")
        
        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return CategoryResponse.from_db_model(category)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")


@router.get("/", response_model=List[CompanionResponse])
async def get_companions(
    user_id: str = Query(..., description="User ID to filter companions"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of companions to return"),
    offset: int = Query(0, ge=0, description="Number of companions to skip"),
    db: AsyncSession = Depends(get_db)
):
    """Get companions for a user"""
    try:
        query = select(Companion).where(Companion.user_id == user_id)
        
        if category_id:
            query = query.where(Companion.category_id == category_id)
        
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        companions = result.scalars().all()
        
        return [CompanionResponse.from_db_model(comp) for comp in companions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companions: {str(e)}")


@router.get("/{companion_id}", response_model=CompanionResponse)
async def get_companion(
    companion_id: str,
    user_id: str = Query(..., description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific companion"""
    try:
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == companion_id,
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        return CompanionResponse.from_db_model(companion)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companion: {str(e)}")


@router.post("/", response_model=CompanionResponse)
async def create_companion(
    companion_data: CompanionCreate,
    user_id: str = Query(..., description="User ID"),
    user_name: str = Query(..., description="User name"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new companion"""
    try:
        # Verify category exists
        result = await db.execute(select(Category).where(Category.id == companion_data.category_id))
        category = result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        
        # Create companion
        companion = Companion(
            user_id=user_id,
            user_name=user_name,
            name=companion_data.name,
            short_description=companion_data.short_description,
            character_description=companion_data.character_description,
            category_id=companion_data.category_id,
            src=companion_data.src,
            humor=companion_data.personality_traits.humor,
            empathy=companion_data.personality_traits.empathy,
            assertiveness=companion_data.personality_traits.assertiveness,
            sarcasm=companion_data.personality_traits.sarcasm,
            hate_moderation=companion_data.moderation_settings.hate_moderation,
            harassment_moderation=companion_data.moderation_settings.harassment_moderation,
            violence_moderation=companion_data.moderation_settings.violence_moderation,
            self_harm_moderation=companion_data.moderation_settings.self_harm_moderation,
            sexual_moderation=companion_data.moderation_settings.sexual_moderation
        )
        
        db.add(companion)
        await db.commit()
        await db.refresh(companion)
        
        return CompanionResponse.from_db_model(companion)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create companion: {str(e)}")


@router.put("/{companion_id}", response_model=CompanionResponse)
async def update_companion(
    companion_id: str,
    companion_data: CompanionUpdate,
    user_id: str = Query(..., description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """Update a companion"""
    try:
        # Get existing companion
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == companion_id,
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # Update fields
        update_data = companion_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "personality_traits" and value:
                companion.humor = value.get("humor", companion.humor)
                companion.empathy = value.get("empathy", companion.empathy)
                companion.assertiveness = value.get("assertiveness", companion.assertiveness)
                companion.sarcasm = value.get("sarcasm", companion.sarcasm)
            elif field == "moderation_settings" and value:
                companion.hate_moderation = value.get("hate_moderation", companion.hate_moderation)
                companion.harassment_moderation = value.get("harassment_moderation", companion.harassment_moderation)
                companion.violence_moderation = value.get("violence_moderation", companion.violence_moderation)
                companion.self_harm_moderation = value.get("self_harm_moderation", companion.self_harm_moderation)
                companion.sexual_moderation = value.get("sexual_moderation", companion.sexual_moderation)
            else:
                setattr(companion, field, value)
        
        await db.commit()
        await db.refresh(companion)
        
        return CompanionResponse.from_db_model(companion)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update companion: {str(e)}")


@router.delete("/{companion_id}")
async def delete_companion(
    companion_id: str,
    user_id: str = Query(..., description="User ID for authorization"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a companion"""
    try:
        # Get existing companion
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == companion_id,
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        await db.delete(companion)
        await db.commit()
        
        return {"message": "Companion deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete companion: {str(e)}") 