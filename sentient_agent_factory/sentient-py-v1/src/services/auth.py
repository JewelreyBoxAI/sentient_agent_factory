"""
Authentication service - Clerk integration
"""
import os
import jwt
import requests
from typing import Optional, Dict, Any
from functools import lru_cache

class AuthService:
    """Authentication service with Clerk integration"""
    
    def __init__(self):
        self.clerk_secret_key = os.getenv("CLERK_SECRET_KEY", "")
        self.jwt_secret = os.getenv("JWT_SECRET", "dev_jwt_secret")
        self.clerk_api_url = "https://api.clerk.dev/v1"
    
    @staticmethod
    @lru_cache()
    def get_instance():
        """Get singleton instance"""
        return AuthService()
    
    def verify_clerk_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Clerk session token"""
        if not self.clerk_secret_key:
            # Development mode - return test user
            return {
                "user_id": "test-user-123",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.clerk_secret_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.clerk_api_url}/sessions/{token}/verify",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                session_data = response.json()
                return session_data.get("user", {})
            
        except Exception as e:
            print(f"Clerk verification error: {e}")
        
        return None
    
    def get_current_user(self, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get current user from token"""
        if not token:
            return None
        
        # Try Clerk token verification first
        user = self.verify_clerk_token(token)
        if user:
            return user
        
        # Fallback to JWT verification
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError:
            return None
    
    def verify_token(self, token: str) -> bool:
        """Verify authentication token"""
        return self.get_current_user(token) is not None
    
    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token for user"""
        return jwt.encode(user_data, self.jwt_secret, algorithm="HS256")


# Global instance
auth_service = AuthService.get_instance() 