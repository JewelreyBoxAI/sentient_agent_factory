"""
Chat API Routes
Distributed conversation system using LangGraph + Character Agents
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from ...config.database import get_db
from ...models.companion import Companion
from ...models.message import Message, MessageRole
from ...memory.distributed_memory import DistributedMemoryManager, CompanionKey
from ...agents.character_agent import CharacterAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


# ===== PYDANTIC SCHEMAS =====

class ChatMessage(BaseModel):
    """Chat message schema"""
    content: str = Field(min_length=1, max_length=10000)
    role: MessageRole = Field(default=MessageRole.USER)


class ChatRequest(BaseModel):
    """Chat request schema"""
    companion_id: str
    user_id: str
    message: str = Field(min_length=1, max_length=10000)
    model_name: str = Field(default="gpt-4o-mini")


class ChatResponse(BaseModel):
    """Chat response schema"""
    message: str
    companion_id: str
    user_id: str
    message_id: str
    timestamp: str
    processing_time_ms: float


class ConversationHistory(BaseModel):
    """Conversation history schema"""
    messages: List[Dict[str, Any]]
    total_messages: int
    companion_name: str


class MemoryStats(BaseModel):
    """Memory statistics schema"""
    thread_id: str
    total_messages: int
    user_messages: int
    ai_messages: int
    has_distributed_state: bool


# ===== CHAT ENDPOINTS =====

@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send message to companion and get AI response
    USES DISTRIBUTED MEMORY - NO SINGLETON PATTERN!
    """
    import time
    start_time = time.time()
    
    try:
        # Verify companion exists and belongs to user
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == chat_request.companion_id,
                    Companion.user_id == chat_request.user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # Initialize distributed memory system
        companion_key = CompanionKey(
            companion_id=chat_request.companion_id,
            user_id=chat_request.user_id,
            model_name=chat_request.model_name
        )
        
        memory_manager = DistributedMemoryManager(companion_key, db)
        await memory_manager.initialize_vector_store()
        
        # Save user message to distributed storage
        await memory_manager.add_message(chat_request.message, MessageRole.USER)
        
        # Initialize character agent
        character_agent = CharacterAgent(
            companion=companion,
            memory_manager=memory_manager,
            model_name=chat_request.model_name
        )
        
        # Generate AI response using character agent
        ai_response = await character_agent.generate_response(
            user_input=chat_request.message,
            conversation_context=await memory_manager.get_conversation_history()
        )
        
        # Save AI response to distributed storage
        await memory_manager.add_message(ai_response, MessageRole.ASSISTANT)
        
        # Create response message record
        response_message = Message(
            content=ai_response,
            role=MessageRole.ASSISTANT,
            companion_id=chat_request.companion_id,
            user_id=chat_request.user_id
        )
        
        db.add(response_message)
        await db.commit()
        await db.refresh(response_message)
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"💬 [Chat] Generated response for {companion_key.thread_id} in {processing_time:.1f}ms")
        
        return ChatResponse(
            message=ai_response,
            companion_id=chat_request.companion_id,
            user_id=chat_request.user_id,
            message_id=str(response_message.id),
            timestamp=response_message.created_at.isoformat(),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ [Chat] Error generating response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@router.get("/history/{companion_id}", response_model=ConversationHistory)
async def get_conversation_history(
    companion_id: str,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history for a companion"""
    try:
        # Verify companion exists and belongs to user
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == companion_id,
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # Get messages from database
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.companion_id == companion_id,
                    Message.user_id == user_id
                )
            ).order_by(Message.created_at.desc()).offset(offset).limit(limit)
        )
        
        messages = result.scalars().all()
        
        # Convert to response format
        message_list = []
        for msg in reversed(messages):  # Reverse to get chronological order
            message_list.append({
                "id": str(msg.id),
                "content": msg.content,
                "role": msg.role.value,
                "timestamp": msg.created_at.isoformat(),
                "companion_id": str(msg.companion_id),
                "user_id": msg.user_id
            })
        
        # Get total message count
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Message.id)).where(
                and_(
                    Message.companion_id == companion_id,
                    Message.user_id == user_id
                )
            )
        )
        total_count = result.scalar()
        
        return ConversationHistory(
            messages=message_list,
            total_messages=total_count,
            companion_name=companion.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Chat] Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation history: {str(e)}")


@router.delete("/history/{companion_id}")
async def clear_conversation(
    companion_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Clear conversation history for a companion"""
    try:
        # Verify companion exists and belongs to user
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == companion_id,
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # Clear distributed memory
        companion_key = CompanionKey(
            companion_id=companion_id,
            user_id=user_id
        )
        
        memory_manager = DistributedMemoryManager(companion_key, db)
        await memory_manager.clear_conversation()
        
        # Clear database messages
        await db.execute(
            Message.__table__.delete().where(
                and_(
                    Message.companion_id == companion_id,
                    Message.user_id == user_id
                )
            )
        )
        
        await db.commit()
        
        logger.info(f"🧹 [Chat] Cleared conversation for {companion_key.thread_id}")
        
        return {"message": "Conversation history cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ [Chat] Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {str(e)}")


@router.get("/memory/stats/{companion_id}", response_model=MemoryStats)
async def get_memory_statistics(
    companion_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get memory statistics for a companion conversation"""
    try:
        # Verify companion exists and belongs to user
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == companion_id,
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # Initialize distributed memory system
        companion_key = CompanionKey(
            companion_id=companion_id,
            user_id=user_id
        )
        
        memory_manager = DistributedMemoryManager(companion_key, db)
        stats = await memory_manager.get_memory_statistics()
        
        return MemoryStats(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Chat] Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory statistics: {str(e)}")


@router.post("/semantic-search/{companion_id}")
async def semantic_search(
    companion_id: str,
    user_id: str = Query(..., description="User ID for authorization"),
    query: str = Query(..., min_length=1, max_length=1000, description="Search query"),
    k: int = Query(default=5, ge=1, le=20, description="Number of results to return"),
    db: AsyncSession = Depends(get_db)
):
    """Perform semantic search on conversation history"""
    try:
        # Verify companion exists and belongs to user
        result = await db.execute(
            select(Companion).where(
                and_(
                    Companion.id == companion_id,
                    Companion.user_id == user_id
                )
            )
        )
        companion = result.scalar_one_or_none()
        
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # Initialize distributed memory system
        companion_key = CompanionKey(
            companion_id=companion_id,
            user_id=user_id
        )
        
        memory_manager = DistributedMemoryManager(companion_key, db)
        await memory_manager.initialize_vector_store()
        
        # Perform semantic search
        results = await memory_manager.semantic_search(query, k=k)
        
        return {
            "query": query,
            "results": results,
            "companion_id": companion_id,
            "total_results": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Chat] Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform semantic search: {str(e)}")


# ===== WEBSOCKET ENDPOINT =====

@router.websocket("/ws/{companion_id}")
async def websocket_chat(
    websocket: WebSocket,
    companion_id: str,
    user_id: str
):
    """
    WebSocket endpoint for real-time chat
    Maintains persistent connection with distributed memory
    """
    await websocket.accept()
    
    try:
        # Initialize components (simplified for prototype)
        logger.info(f"🔌 [WebSocket] Connected: {user_id} -> {companion_id}")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Echo back for prototype (implement full chat logic later)
            await websocket.send_text(f"Echo: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"🔌 [WebSocket] Disconnected: {user_id} -> {companion_id}")
    except Exception as e:
        logger.error(f"❌ [WebSocket] Error: {e}")
        await websocket.close() 