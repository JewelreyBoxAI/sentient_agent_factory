"""
Companion CRUD API Routes
Frontend-compatible endpoints for AI character management
"""
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from ...config.database import get_db
from ...models.companion import Companion, Category
from ...services.auth import get_current_user
from ...services.cloudinary import upload_avatar

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
    personality_traits: PersonalityTraits
    moderation_settings: ModerationSettings
    
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
            personality_traits=PersonalityTraits(
                humor=companion.humor,
                empathy=companion.empathy,
                assertiveness=companion.assertiveness,
                sarcasm=companion.sarcasm
            ),
            moderation_settings=ModerationSettings(
                hate_moderation=companion.hate_moderation,
                harassment_moderation=companion.harassment_moderation,
                violence_moderation=companion.violence_moderation,
                self_harm_moderation=companion.self_harm_moderation,
                sexual_moderation=companion.sexual_moderation
            )
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
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Get specific companion by ID"""
    try:
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == uuid.UUID(companion_id),
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        return CompanionResponse.from_db_model(companion)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companion: {str(e)}")


@router.post("/", response_model=CompanionResponse)
async def create_companion_with_avatar(
    name: str = Form(...),
    short_description: str = Form(...),
    character_description: str = Form(default="{}"),
    category_id: str = Form(...),
    humor: int = Form(default=3, ge=1, le=5),
    empathy: int = Form(default=3, ge=1, le=5),
    assertiveness: int = Form(default=3, ge=1, le=5),
    sarcasm: int = Form(default=3, ge=1, le=5),
    hate_moderation: int = Form(default=3, ge=1, le=5),
    harassment_moderation: int = Form(default=3, ge=1, le=5),
    violence_moderation: int = Form(default=3, ge=1, le=5),
    self_harm_moderation: int = Form(default=3, ge=1, le=5),
    sexual_moderation: int = Form(default=3, ge=1, le=5),
    avatar_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Create new companion with avatar upload
    
    Professional multipart/form-data endpoint that:
    1. Validates all companion data
    2. Uploads avatar to Cloudinary with optimizations
    3. Creates companion with Cloudinary URL
    4. Returns complete companion object
    """
    try:
        # 1. Validate category exists
        result = await db.execute(
            select(Category).where(Category.id == uuid.UUID(category_id))
        )
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # 2. Upload avatar to Cloudinary
        cloudinary_result = await upload_avatar(avatar_file, user_id, name)
        avatar_url = cloudinary_result["url"]
        
        # 3. Parse character description JSON
        try:
            import json
            character_desc = json.loads(character_description)
        except:
            character_desc = {"description": character_description}
        
        # 4. Create companion with Cloudinary URL
        new_companion = Companion(
            user_id=user_id,
            user_name="User",  # TODO: Get from Clerk
            name=name,
            short_description=short_description,
            character_description=character_desc,
            category_id=uuid.UUID(category_id),
            src=avatar_url,  # Cloudinary URL
            humor=humor,
            empathy=empathy,
            assertiveness=assertiveness,
            sarcasm=sarcasm,
            hate_moderation=hate_moderation,
            harassment_moderation=harassment_moderation,
            violence_moderation=violence_moderation,
            self_harm_moderation=self_harm_moderation,
            sexual_moderation=sexual_moderation
        )
        
        db.add(new_companion)
        await db.commit()
        await db.refresh(new_companion)
        
        return CompanionResponse.from_db_model(new_companion)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create companion: {str(e)}")


@router.put("/{companion_id}", response_model=CompanionResponse)
async def update_companion(
    companion_id: str,
    companion_data: CompanionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Update a companion"""
    try:
        # Get existing companion
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == uuid.UUID(companion_id),
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
                companion.humor = value.humor
                companion.empathy = value.empathy
                companion.assertiveness = value.assertiveness
                companion.sarcasm = value.sarcasm
            elif field == "moderation_settings" and value:
                companion.hate_moderation = value.hate_moderation
                companion.harassment_moderation = value.harassment_moderation
                companion.violence_moderation = value.violence_moderation
                companion.self_harm_moderation = value.self_harm_moderation
                companion.sexual_moderation = value.sexual_moderation
            elif field == "category_id" and value:
                companion.category_id = uuid.UUID(value)
            else:
                setattr(companion, field, value)
        
        await db.commit()
        await db.refresh(companion)
        
        return CompanionResponse.from_db_model(companion)
    except HTTPException as e:
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update companion: {str(e)}")


@router.delete("/{companion_id}")
async def delete_companion(
    companion_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Delete companion"""
    try:
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == uuid.UUID(companion_id),
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # TODO: Delete from Cloudinary as well
        await db.delete(companion)
        await db.commit()
        
        return {"message": "Companion deleted successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete companion: {str(e)}") 