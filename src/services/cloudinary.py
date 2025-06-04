"""
Cloudinary service for image upload and management
"""
import logging
from typing import Dict, Any, Optional
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import HTTPException, UploadFile
import io
from PIL import Image

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

# Professional validation settings
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_DIMENSIONS = (50, 50)
MAX_DIMENSIONS = (4000, 4000)


def validate_image_file(file: UploadFile) -> None:
    """
    Professional image validation
    
    Args:
        file: The uploaded file to validate
        
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file extension
    if file.filename:
        extension = '.' + file.filename.split('.')[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Read file data for validation
    file_data = file.file.read()
    file.file.seek(0)  # Reset file pointer
    
    # Check file size
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    
    # Validate image with PIL
    try:
        with Image.open(io.BytesIO(file_data)) as img:
            width, height = img.size
            
            # Check dimensions
            if width < MIN_DIMENSIONS[0] or height < MIN_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Image too small. Minimum: {MIN_DIMENSIONS[0]}x{MIN_DIMENSIONS[1]}px"
                )
            
            if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Image too large. Maximum: {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]}px"
                )
                
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail="Invalid image file")


async def upload_avatar(file: UploadFile, user_id: str, companion_name: str = None) -> Dict[str, Any]:
    """
    Upload avatar image to Cloudinary with professional validation
    
    Args:
        file: The uploaded file
        user_id: User ID for organizing uploads
        companion_name: Optional companion name for the filename
        
    Returns:
        Dict containing Cloudinary response with URL and metadata
    """
    try:
        # Professional validation
        validate_image_file(file)
        
        # Generate secure public_id
        safe_companion_name = companion_name.replace(' ', '_').lower() if companion_name else 'avatar'
        public_id = f"sentient_ai/avatars/{user_id}/{safe_companion_name}"
        
        # Upload to Cloudinary with professional settings
        result = cloudinary.uploader.upload(
            file.file,
            public_id=public_id,
            resource_type="image",
            transformation=[
                {"width": 400, "height": 400, "crop": "fill", "gravity": "auto"},
                {"quality": "auto:good", "fetch_format": "auto"}
            ],
            tags=["avatar", "sentient_ai", user_id],
            overwrite=True,  # Replace existing avatar
            invalidate=True,  # Clear CDN cache
            eager=[
                {"width": 100, "height": 100, "crop": "fill", "gravity": "auto"},  # Thumbnail
                {"width": 200, "height": 200, "crop": "fill", "gravity": "auto"}   # Medium
            ]
        )
        
        logger.info(f"✅ [CLOUDINARY] Avatar uploaded: {result.get('public_id')}")
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "resource_type": result.get("resource_type"),
            "created_at": result.get("created_at"),
            "bytes": result.get("bytes"),
            "thumbnail_url": f"{result.get('secure_url').replace('/upload/', '/upload/w_100,h_100,c_fill,g_auto/')}"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ [CLOUDINARY] Avatar upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def upload_profile_picture(file: UploadFile, user_id: str) -> Dict[str, Any]:
    """
    Upload user profile picture to Cloudinary with professional validation
    
    Args:
        file: The uploaded file
        user_id: User ID for organizing uploads
        
    Returns:
        Dict containing Cloudinary response with URL and metadata
    """
    try:
        # Professional validation
        validate_image_file(file)
        
        # Generate secure public_id
        public_id = f"sentient_ai/profiles/{user_id}/profile"
        
        # Upload to Cloudinary with professional settings
        result = cloudinary.uploader.upload(
            file.file,
            public_id=public_id,
            resource_type="image",
            transformation=[
                {"width": 200, "height": 200, "crop": "fill", "gravity": "face"},
                {"quality": "auto:good", "fetch_format": "auto"}
            ],
            tags=["profile", "sentient_ai", user_id],
            overwrite=True,  # Replace existing profile
            invalidate=True,  # Clear CDN cache
            eager=[
                {"width": 50, "height": 50, "crop": "fill", "gravity": "face"},   # Small
                {"width": 100, "height": 100, "crop": "fill", "gravity": "face"}  # Medium
            ]
        )
        
        logger.info(f"✅ [CLOUDINARY] Profile picture uploaded: {result.get('public_id')}")
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "resource_type": result.get("resource_type"),
            "created_at": result.get("created_at"),
            "bytes": result.get("bytes"),
            "small_url": f"{result.get('secure_url').replace('/upload/', '/upload/w_50,h_50,c_fill,g_face/')}"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ [CLOUDINARY] Profile upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def delete_image(public_id: str) -> Dict[str, Any]:
    """
    Delete image from Cloudinary with validation
    
    Args:
        public_id: The Cloudinary public ID of the image to delete
        
    Returns:
        Dict containing deletion result
    """
    try:
        # Validate public_id format for security
        if not public_id.startswith('sentient_ai/'):
            raise HTTPException(status_code=403, detail="Invalid image reference")
        
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
        
        logger.info(f"✅ [CLOUDINARY] Image deleted: {public_id}")
        
        return {
            "result": result.get("result"),
            "public_id": public_id,
            "success": result.get("result") == "ok"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ [CLOUDINARY] Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


def get_optimized_url(public_id: str, width: int = 400, height: int = 400) -> str:
    """
    Generate optimized URL for existing Cloudinary image
    
    Args:
        public_id: The Cloudinary public ID
        width: Desired width
        height: Desired height
        
    Returns:
        Optimized image URL
    """
    try:
        url = cloudinary.utils.cloudinary_url(
            public_id,
            width=width,
            height=height,
            crop="fill",
            gravity="auto",
            quality="auto:good",
            fetch_format="auto",
            secure=True,
            sign_url=True
        )[0]
        
        return url
        
    except Exception as e:
        logger.error(f"❌ [CLOUDINARY] URL generation failed: {e}")
        return ""


def get_transformation_url(public_id: str, transformations: Dict[str, Any]) -> str:
    """
    Generate URL with custom transformations
    
    Args:
        public_id: The Cloudinary public ID
        transformations: Dict of transformation parameters
        
    Returns:
        Transformed image URL
    """
    try:
        url = cloudinary.utils.cloudinary_url(
            public_id,
            secure=True,
            sign_url=True,
            **transformations
        )[0]
        
        return url
        
    except Exception as e:
        logger.error(f"❌ [CLOUDINARY] Transformation URL failed: {e}")
        return "" 