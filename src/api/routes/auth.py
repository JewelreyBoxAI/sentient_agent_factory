"""
Authentication API routes
Working implementation for development
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from ...services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class UserResponse(BaseModel):
    """User response model"""
    user_id: str
    user_name: str
    email: str


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current user info"""
    try:
        user = AuthService.get_current_user(
            credentials.credentials if credentials else None
        )
        return UserResponse(**user)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")


@router.post("/verify")
async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Verify authentication token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No token provided")
    
    is_valid = AuthService.verify_token(credentials.credentials)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"valid": True, "message": "Token is valid"}

# TODO: Implement auth endpoints if not using Clerk
# - POST /auth/login
# - POST /auth/logout  
# - GET /auth/me 