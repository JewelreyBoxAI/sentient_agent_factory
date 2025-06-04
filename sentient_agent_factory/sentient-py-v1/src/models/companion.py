"""
Companion and Category models
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..config.database import Base


class Category(Base):
    """Category model for organizing companions"""
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    
    # Relationships
    companions = relationship("Companion", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"


class Companion(Base):
    """Companion model for AI characters"""
    __tablename__ = "companions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    short_description = Column(String, nullable=False)
    character_description = Column(JSON, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    src = Column(String, nullable=False)  # Image URL
    
    # Trait scales (1-5)
    humor = Column(Integer, default=3)
    empathy = Column(Integer, default=3)
    assertiveness = Column(Integer, default=3)
    sarcasm = Column(Integer, default=3)
    
    # Moderation metrics (1-5)
    hate_moderation = Column(Integer, default=3)
    harassment_moderation = Column(Integer, default=3)
    violence_moderation = Column(Integer, default=3)
    self_harm_moderation = Column(Integer, default=3)
    sexual_moderation = Column(Integer, default=3)
    
    # Relationships
    category = relationship("Category", back_populates="companions")
    messages = relationship("Message", back_populates="companion", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Companion(id={self.id}, name={self.name}, user_id={self.user_id})>"
    
    @property
    def character_traits(self) -> Dict[str, int]:
        """Get character traits as dictionary"""
        return {
            "humor": self.humor,
            "empathy": self.empathy,
            "assertiveness": self.assertiveness,
            "sarcasm": self.sarcasm
        }
    
    @property
    def moderation_settings(self) -> Dict[str, int]:
        """Get moderation settings as dictionary"""
        return {
            "hate_moderation": self.hate_moderation,
            "harassment_moderation": self.harassment_moderation,
            "violence_moderation": self.violence_moderation,
            "self_harm_moderation": self.self_harm_moderation,
            "sexual_moderation": self.sexual_moderation
        } 