"""
LangGraph Character Agent - JSON-driven with standardized prompt chain template
Follows the same pattern as your existing Python projects
"""
import logging
from typing import Dict, Any, List, TypedDict
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..memory.distributed_memory import DistributedMemoryManager
from ..config.settings import get_settings
from ..models.companion import Companion

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Standardized chat request model"""
    user_input: str
    history: list


class ConversationState(TypedDict):
    """State for the conversation graph"""
    messages: List[BaseMessage]
    companion_id: str
    user_id: str
    agent_role: str  # JSON-driven role definition
    character_traits: Dict[str, int]
    current_input: str
    response: str
    memory_context: List[str]


class CharacterAgent:
    """
    JSON-driven Character Agent following standardized prompt chain template
    Each agent runs off a JSON object using the same custom prompt chain template
    """
    
    def __init__(self, companion: Companion, memory_manager: DistributedMemoryManager):
        self.companion = companion
        self.memory_manager = memory_manager
        self.settings = get_settings()
        
        # ─── LLM + MEMORY (Following your standardized pattern) ──────────────
        self.memory = InMemoryChatMessageHistory(return_messages=True)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            max_tokens=1024, 
            temperature=0.9
        )
        
        # ─── JSON-DRIVEN AGENT ROLE ─────────────────────────────────────────
        self.agent_role = self._build_agent_role_from_json()
        
        # ─── STANDARDIZED PROMPT TEMPLATE ───────────────────────────────────
        self.prompt_template = self._create_standardized_prompt_template()
        
        # ─── CHAIN (Following your pattern: prompt_template | llm) ──────────
        self.chain = self.prompt_template | self.llm
        
        # Build the LangGraph workflow
        self.graph = self._build_character_graph()
        
        logger.info(f"🎭 [CharacterAgent] Initialized: {companion.name}")
    
    def _build_agent_role_from_json(self) -> str:
        """
        Build agent role from JSON character description
        Following AGENT_ROLES pattern from your existing projects
        """
        char_desc = self.companion.character_description
        traits = self.companion.character_traits
        
        # Build standardized agent role from JSON
        role_components = [
            char_desc.get('physicalAppearance', ''),
            char_desc.get('identity', ''),
            char_desc.get('interactionStyle', ''),
            f"Personality traits: Humor={traits.get('humor', 3)}/5, "
            f"Empathy={traits.get('empathy', 3)}/5, "
            f"Assertiveness={traits.get('assertiveness', 3)}/5, "
            f"Sarcasm={traits.get('sarcasm', 3)}/5",
            "Avoid repeating yourself. If forced to repeat and your humor/sarcasm is 4-5, playfully call out the user's repetition."
        ]
        
        # Join like your AGENT_ROLES pattern
        prompt_text = " ".join(role_components) if isinstance(role_components, list) else str(role_components)
        
        return prompt_text
    
    def _create_standardized_prompt_template(self) -> ChatPromptTemplate:
        """
        Create standardized prompt template following your exact pattern:
        SystemMessagePromptTemplate + MessagesPlaceholder + HumanMessagePromptTemplate
        """
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.agent_role),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{user_input}")
        ])
    
    def _build_character_graph(self) -> StateGraph:
        """Build LangGraph workflow using standardized chain"""
        workflow = StateGraph(ConversationState)
        
        # Add nodes that use the standardized prompt chain
        workflow.add_node("memory_retrieval", self._memory_retrieval_node)
        workflow.add_node("standardized_chain_processing", self._standardized_chain_node)
        workflow.add_node("response_finalization", self._response_finalization_node)
        
        # Define flow
        workflow.set_entry_point("memory_retrieval")
        workflow.add_edge("memory_retrieval", "standardized_chain_processing")
        workflow.add_edge("standardized_chain_processing", "response_finalization")
        workflow.add_edge("response_finalization", END)
        
        return workflow.compile(checkpointer=self.memory_manager.checkpointer)
    
    async def _memory_retrieval_node(self, state: ConversationState) -> ConversationState:
        """Retrieve conversation history for the standardized template"""
        logger.info("🧠 [CharacterAgent] Memory retrieval")
        
        try:
            # Get recent messages for history placeholder
            recent_messages = await self.memory_manager.get_conversation_history(limit=10)
            
            # Convert to the format expected by MessagesPlaceholder
            state["memory_context"] = [msg.content for msg in recent_messages[-5:]]
            
        except Exception as e:
            logger.error(f"❌ [CharacterAgent] Memory error: {e}")
            state["memory_context"] = []
        
        return state
    
    async def _standardized_chain_node(self, state: ConversationState) -> ConversationState:
        """
        Process using standardized prompt chain template
        This ensures every agent follows the same pattern: prompt_template | llm
        """
        logger.info("⚡ [CharacterAgent] Standardized chain processing")
        
        try:
            # Prepare input for standardized template
            chain_input = {
                "user_input": state["current_input"],
                "history": state["memory_context"]  # For MessagesPlaceholder
            }
            
            # Use the standardized chain (prompt_template | llm)
            response = await self.chain.ainvoke(chain_input)
            state["response"] = response.content.strip()
            
            logger.info(f"✅ [CharacterAgent] Chain response generated")
            
        except Exception as e:
            logger.error(f"❌ [CharacterAgent] Chain processing error: {e}")
            state["response"] = "I'm having trouble processing that. Please try again."
        
        return state
    
    async def _response_finalization_node(self, state: ConversationState) -> ConversationState:
        """Final processing and validation"""
        logger.info("🎯 [CharacterAgent] Response finalization")
        
        # Add any final processing here (moderation, formatting, etc.)
        # For now, just pass through
        
        return state
    
    async def process_conversation(self, user_input: str) -> str:
        """
        Main conversation processing using JSON-driven standardized chain
        EVERY AGENT uses the same prompt chain template pattern!
        """
        logger.info(f"🎬 [CharacterAgent] Processing: {self.companion.name}")
        
        # Create initial state with JSON-driven role
        initial_state: ConversationState = {
            "messages": [],
            "companion_id": str(self.companion.id),
            "user_id": self.memory_manager.companion_key.user_id,
            "agent_role": self.agent_role,  # JSON-driven role
            "character_traits": self.companion.character_traits,
            "current_input": user_input,
            "response": "",
            "memory_context": []
        }
        
        try:
            # Process through LangGraph with standardized chain
            config = {"configurable": {"thread_id": self.memory_manager.companion_key.thread_id}}
            final_state = await self.graph.ainvoke(initial_state, config)
            
            # Save conversation to distributed memory
            await self.memory_manager.add_message(user_input, "user")
            await self.memory_manager.add_message(final_state["response"], "system")
            
            logger.info("✅ [CharacterAgent] Standardized processing complete")
            return final_state["response"]
            
        except Exception as e:
            logger.error(f"❌ [CharacterAgent] Processing error: {e}")
            return "I'm experiencing technical difficulties. Please try again."
    
    @classmethod
    def from_json_config(cls, json_config: Dict[str, Any], memory_manager: DistributedMemoryManager):
        """
        Create agent from pure JSON configuration
        Enables easy agent creation: CharacterAgent.from_json_config(agent_json)
        """
        # Convert JSON to Companion object
        companion = Companion(
            name=json_config.get("name", "Unknown"),
            character_description=json_config.get("character_description", {}),
            humor=json_config.get("traits", {}).get("humor", 3),
            empathy=json_config.get("traits", {}).get("empathy", 3),
            assertiveness=json_config.get("traits", {}).get("assertiveness", 3),
            sarcasm=json_config.get("traits", {}).get("sarcasm", 3)
        )
        
        return cls(companion, memory_manager) 