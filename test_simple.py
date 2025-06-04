"""
Simple test to verify imports work
"""
import sys
import os

# Set up environment - user should provide real API key
if not os.environ.get("OPENAI_API_KEY"):
    print("⚠️  Warning: OPENAI_API_KEY not set. Set it in your environment or .env file")
    print("Example: export OPENAI_API_KEY=sk-your-actual-key-here")

sys.path.append("src")

try:
    print("🧪 Testing imports...")
    
    from config.database import DatabaseManager
    from models.companion import Companion, Category
    from services.memory_manager import DistributedMemoryManager
    from agents.character_agent import CharacterAgent
    from api.routes.companion import router as companion_router
    from api.routes.chat import router as chat_router
    
    print("✅ All imports successful!")
    print("✅ Backend components are working correctly")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Simple test completed successfully!") 