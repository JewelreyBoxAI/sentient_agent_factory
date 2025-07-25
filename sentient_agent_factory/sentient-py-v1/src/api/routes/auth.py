"""
Authentication API routes
Clerk integration for production deployment
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from ...services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class UserResponse(BaseModel):
    """User response model"""
    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current user info"""
    try:
        user = auth_service.get_current_user(
            credentials.credentials if credentials else None
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        return UserResponse(
            user_id=user.get("user_id", user.get("id", "")),
            email=user.get("email", ""),
            first_name=user.get("first_name"),
            last_name=user.get("last_name")
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/verify")
async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Verify authentication token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No token provided")
    
    is_valid = auth_service.verify_token(credentials.credentials)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"valid": True, "message": "Token is valid"}


@router.post("/logout")
async def logout():
    """Logout endpoint (handled by Clerk on frontend)"""
    return {"message": "Logout successful"}


# Note: Login is handled by Clerk on the frontend
# Users will authenticate through Clerk's components
# and receive session tokens to use with this API