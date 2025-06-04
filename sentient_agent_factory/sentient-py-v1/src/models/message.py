"""
Message model for conversation history
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..config.database import Base


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    SYSTEM = "system"


class Message(Base):
    """Message model for conversation history"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    companion_id = Column(UUID(as_uuid=True), ForeignKey("companions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, nullable=False)
    
    # Relationships
    companion = relationship("Companion", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, companion_id={self.companion_id})>"
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            "id": str(self.id),
            "role": self.role.value,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "companion_id": str(self.companion_id),
            "user_id": self.user_id
        } 