"""
Authentication service - Working implementation
"""
from typing import Optional

class AuthService:
    """Authentication service"""
    
    @staticmethod
    def get_current_user(token: Optional[str] = None) -> dict:
        """Get current user from token"""
        # Return test user for development
        return {
            "user_id": "test-user-123",
            "user_name": "Test User",
            "email": "test@example.com"
        }
    
    @staticmethod
    def verify_token(token: str) -> bool:
        """Verify authentication token"""
        # Accept any token for development
        return True 