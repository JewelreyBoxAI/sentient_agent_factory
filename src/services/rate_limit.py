"""
Rate limiting service
Working in-memory implementation for development
"""
import time
from typing import Dict, Tuple
from collections import defaultdict

class RateLimiter:
    """In-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, user_id: str, window_seconds: int = 60, max_requests: int = 100) -> Tuple[bool, int]:
        """
        Check if request is allowed for user
        Returns (is_allowed, remaining_requests)
        """
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests outside the window
        cutoff = now - window_seconds
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff]
        
        # Check if under limit
        if len(user_requests) < max_requests:
            user_requests.append(now)
            return True, max_requests - len(user_requests)
        
        return False, 0

# Global rate limiter instance
rate_limiter = RateLimiter() 