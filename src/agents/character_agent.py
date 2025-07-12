import logging
from typing import List, TypedDict, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from ..memory.distributed_memory import DistributedMemoryManager
from ..config.settings import get_settings
from ..models.companion import Companion

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    user_input: str
    history: list

class ConversationState(TypedDict):
    messages: List[BaseMessage]
    current_input: str
    response: str
    history: List[BaseMessage]

class CharacterAgent:
    def __init__(self, companion: Companion, memory_manager: DistributedMemoryManager):
        self.companion = companion
        self.memory_manager = memory_manager
        self.settings = get_settings()
        
        self.llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=1024, temperature=0.9)
        self.memory = InMemoryChatMessageHistory()

        self.system_prompt = self._simple_json_prompt()
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("placeholder", "{history}"),
            ("human", "{user_input}")
        ])

        self.chain = self.prompt_template | self.llm
        self.graph = self._build_character_graph()

        logger.info(f"🎭 CharacterAgent initialized: {companion.name}")

    def _simple_json_prompt(self) -> str:
        desc = self.companion.character_description
        traits = self.companion.character_traits
        return (
            f"You are {desc.get('identity', 'an AI character')}. "
            f"Style: {desc.get('interactionStyle', 'friendly')}. "
            f"Traits - Humor: {traits.get('humor',3)}/5, Empathy: {traits.get('empathy',3)}/5, "
            f"Assertiveness: {traits.get('assertiveness',3)}/5, Sarcasm: {traits.get('sarcasm',3)}/5. "
            "Avoid repetition; playfully mention it if humor or sarcasm is high."
        )

    def _build_character_graph(self) -> StateGraph:
        graph = StateGraph(ConversationState)
        graph.add_node("retrieve_history", self.retrieve_history)
        graph.add_node("generate_response", self.generate_response)
        graph.set_entry_point("retrieve_history")
        graph.add_edge("retrieve_history", "generate_response")
        graph.add_edge("generate_response", END)
        return graph.compile(checkpointer=self.memory_manager.checkpointer)

    async def retrieve_history(self, state: ConversationState) -> ConversationState:
        try:
            recent_msgs = await self.memory_manager.get_conversation_history(limit=10)
            state["history"] = recent_msgs[-5:]
        except Exception as e:
            logger.error(f"Memory retrieval error: {e}")
            state["history"] = []
        return state

    async def generate_response(self, state: ConversationState) -> ConversationState:
        try:
            formatted_history = [
                HumanMessage(content=m.content) if m.type == "human" else AIMessage(content=m.content)
                for m in state.get("history", [])
            ]
            chain_input = {
                "user_input": state["current_input"],
                "history": formatted_history
            }
            res = await self.chain.ainvoke(chain_input)
            state["response"] = res.content.strip()
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            state["response"] = "I'm having issues right now."
        return state

    async def process_conversation(self, user_input: str) -> str:
        initial_state = {
            "messages": [],
            "current_input": user_input,
            "response": "",
            "history": []
        }
        try:
            config = {"configurable": {"thread_id": self.memory_manager.companion_key.thread_id}}
            final_state = await self.graph.ainvoke(initial_state, config)

            await self.memory_manager.add_message(user_input, "user")
            await self.memory_manager.add_message(final_state["response"], "system")

            return final_state["response"]
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return "Technical difficulty—try again."

    @classmethod
    def from_json_config(cls, json_config: Dict[str, Any], memory_manager: DistributedMemoryManager):
        companion = Companion(
            name=json_config.get("name", "Unknown"),
            character_description=json_config.get("character_description", {}),
            humor=json_config.get("traits", {}).get("humor", 3),
            empathy=json_config.get("traits", {}).get("empathy", 3),
            assertiveness=json_config.get("traits", {}).get("assertiveness", 3),
            sarcasm=json_config.get("traits", {}).get("sarcasm", 3)
        )
        return cls(companion, memory_manager)
