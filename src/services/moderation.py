"""
Content moderation service
"""
import logging
from typing import Dict, Any
import openai
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def moderate_input(text: str) -> Dict[str, Any]:
    """
    Moderate user input for inappropriate content
    Uses OpenAI moderation API
    """
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.moderations.create(input=text)
        result = response.results[0]
        
        return {
            "flagged": result.flagged,
            "categories": result.categories.__dict__ if result.categories else {},
            "category_scores": result.category_scores.__dict__ if result.category_scores else {}
        }
        
    except Exception as e:
        logger.error(f"❌ [MODERATION] Error moderating input: {e}")
        # Fail safe - don't block if moderation fails
        return {"flagged": False, "error": str(e)}


async def moderate_response(text: str) -> Dict[str, Any]:
    """
    Moderate AI response for inappropriate content
    """
    try:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.moderations.create(input=text)
        result = response.results[0]
        
        return {
            "flagged": result.flagged,
            "categories": result.categories.__dict__ if result.categories else {},
            "category_scores": result.category_scores.__dict__ if result.category_scores else {}
        }
        
    except Exception as e:
        logger.error(f"❌ [MODERATION] Error moderating response: {e}")
        return {"flagged": False, "error": str(e)} 