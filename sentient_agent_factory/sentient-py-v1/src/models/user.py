"""
User-related models for subscriptions and API limits
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from ..config.database import Base


class UserSubscription(Base):
    """User subscription model for Stripe integration"""
    __tablename__ = "user_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, unique=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    stripe_price_id = Column(String, nullable=True)
    stripe_current_period_end = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<UserSubscription(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        if not self.stripe_current_period_end:
            return False
        return self.stripe_current_period_end > datetime.utcnow()


class UserApiLimit(Base):
    """User API usage limit tracking"""
    __tablename__ = "user_api_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, unique=True, nullable=False)
    count = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f"<UserApiLimit(id={self.id}, user_id={self.user_id}, count={self.count})>" 