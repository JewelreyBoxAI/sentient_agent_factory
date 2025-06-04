"""
Upload routes for Cloudinary image management
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

from ...services.cloudinary import (
    upload_avatar, 
    upload_profile_picture, 
    delete_image,
    get_optimized_url,
    get_transformation_url
)
from ...services.auth import get_current_user

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/avatar", response_model=Dict[str, Any])
async def upload_companion_avatar(
    file: UploadFile = File(...),
    companion_name: Optional[str] = Query(None, description="Optional companion name for organizing uploads"),
    user_id: str = Depends(get_current_user)
):
    """
    Upload avatar image for companion
    
    - **file**: Image file (JPG, PNG, GIF, WebP)
    - **companion_name**: Optional companion name for file organization
    - Returns optimized Cloudinary URL and metadata
    """
    try:
        result = await upload_avatar(file, user_id, companion_name)
        
        return {
            "success": True,
            "message": "Avatar uploaded successfully",
            "data": result
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/profile", response_model=Dict[str, Any])
async def upload_user_profile_picture(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Upload user profile picture
    
    - **file**: Image file (JPG, PNG, GIF, WebP)
    - Returns optimized Cloudinary URL and metadata
    """
    try:
        result = await upload_profile_picture(file, user_id)
        
        return {
            "success": True,
            "message": "Profile picture uploaded successfully",
            "data": result
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/image/{public_id:path}")
async def delete_uploaded_image(
    public_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete image from Cloudinary
    
    - **public_id**: Cloudinary public ID of the image to delete
    - User can only delete their own images (verified by path structure)
    """
    try:
        # Security check: ensure user can only delete their own images
        if not (f"/{user_id}/" in public_id or public_id.startswith(f"avatars/{user_id}/") or public_id.startswith(f"profiles/{user_id}/")):
            raise HTTPException(status_code=403, detail="You can only delete your own images")
        
        result = await delete_image(public_id)
        
        return {
            "success": True,
            "message": "Image deleted successfully",
            "data": result
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/optimize/{public_id:path}")
async def get_optimized_image_url(
    public_id: str,
    width: int = Query(400, ge=50, le=2000, description="Image width (50-2000px)"),
    height: int = Query(400, ge=50, le=2000, description="Image height (50-2000px)")
):
    """
    Get optimized URL for existing Cloudinary image
    
    - **public_id**: Cloudinary public ID
    - **width**: Desired width (50-2000px)
    - **height**: Desired height (50-2000px)
    - Returns optimized image URL
    """
    try:
        url = get_optimized_url(public_id, width, height)
        
        if not url:
            raise HTTPException(status_code=404, detail="Image not found or optimization failed")
        
        return {
            "success": True,
            "url": url,
            "width": width,
            "height": height,
            "public_id": public_id
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/transform/{public_id:path}")
async def get_transformed_image_url(
    public_id: str,
    transformations: Dict[str, Any]
):
    """
    Get custom transformation URL for existing Cloudinary image
    
    - **public_id**: Cloudinary public ID
    - **transformations**: Dict of Cloudinary transformation parameters
    
    Example transformations:
    ```json
    {
        "width": 500,
        "height": 500,
        "crop": "fill",
        "gravity": "face",
        "quality": "auto",
        "fetch_format": "auto",
        "effect": "sepia"
    }
    ```
    """
    try:
        url = get_transformation_url(public_id, transformations)
        
        if not url:
            raise HTTPException(status_code=404, detail="Image not found or transformation failed")
        
        return {
            "success": True,
            "url": url,
            "public_id": public_id,
            "transformations": transformations
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transformation failed: {str(e)}")


@router.get("/health")
async def upload_service_health():
    """Health check for upload service"""
    return {
        "service": "Upload Service",
        "status": "healthy",
        "cloudinary": "configured"
    } 