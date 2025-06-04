#!/usr/bin/env python3
"""
API Testing Script for Sentient AI Backend
Tests all CRUD endpoints with real data
"""
import asyncio
import httpx
import os
import sys
import json
import time
from pathlib import Path

# Set environment variables for prototype
os.environ["OPENAI_API_KEY"] = "sk-test-key-placeholder"
os.environ["DEBUG"] = "true"

# Add src to path
sys.path.append("src")

BASE_URL = "http://127.0.0.1:8000"

async def test_companion_apis():
    """Test companion CRUD operations"""
    print("🧪 Testing Companion APIs...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Create category
            print("\n1️⃣ Creating test category...")
            response = await client.post(
                f"{BASE_URL}/companions/categories",
                params={"name": "AI Assistants"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                category = response.json()
                category_id = category["id"]
                print(f"✅ Created category: {category['name']} (ID: {category_id})")
            else:
                print(f"❌ Failed to create category: {response.text}")
                return False
            
            # Test 2: Create companion
            print("\n2️⃣ Creating test companion...")
            companion_data = {
                "name": "Alex the Helper",
                "short_description": "A friendly AI assistant that loves to help with coding and creative tasks",
                "character_description": {
                    "role": "helpful assistant",
                    "personality": "friendly, enthusiastic, knowledgeable",
                    "expertise": ["coding", "creative writing", "problem solving"]
                },
                "category_id": category_id,
                "src": "https://example.com/alex-avatar.png",
                "personality_traits": {
                    "humor": 4,
                    "empathy": 5,
                    "assertiveness": 3,
                    "sarcasm": 2
                },
                "moderation_settings": {
                    "hate_moderation": 4,
                    "harassment_moderation": 4,
                    "violence_moderation": 4,
                    "self_harm_moderation": 5,
                    "sexual_moderation": 4
                }
            }
            
            response = await client.post(
                f"{BASE_URL}/companions/",
                json=companion_data,
                params={"user_id": "test-user-123", "user_name": "Test User"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                companion = response.json()
                companion_id = companion["id"]
                print(f"✅ Created companion: {companion['name']} (ID: {companion_id})")
            else:
                print(f"❌ Failed to create companion: {response.text}")
                return False
            
            # Test 3: Get companions list
            print("\n3️⃣ Fetching companions list...")
            response = await client.get(
                f"{BASE_URL}/companions/",
                params={"user_id": "test-user-123"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                companions = response.json()
                print(f"✅ Found {len(companions)} companions")
                for comp in companions:
                    print(f"   - {comp['name']}: {comp['short_description'][:50]}...")
            else:
                print(f"❌ Failed to fetch companions: {response.text}")
                return False
            
            # Test 4: Get specific companion
            print("\n4️⃣ Fetching specific companion...")
            response = await client.get(
                f"{BASE_URL}/companions/{companion_id}",
                params={"user_id": "test-user-123"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                companion = response.json()
                print(f"✅ Retrieved companion: {companion['name']}")
                print(f"   Personality: humor={companion['humor']}, empathy={companion['empathy']}")
            else:
                print(f"❌ Failed to fetch companion: {response.text}")
                return False
            
            # Test 5: Update companion
            print("\n5️⃣ Updating companion...")
            update_data = {
                "short_description": "An even more helpful AI assistant!",
                "personality_traits": {
                    "humor": 5,
                    "empathy": 5,
                    "assertiveness": 4,
                    "sarcasm": 1
                }
            }
            
            response = await client.put(
                f"{BASE_URL}/companions/{companion_id}",
                json=update_data,
                params={"user_id": "test-user-123"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                updated_companion = response.json()
                print(f"✅ Updated companion: {updated_companion['short_description']}")
                print(f"   New humor level: {updated_companion['humor']}")
            else:
                print(f"❌ Failed to update companion: {response.text}")
                return False
            
            return companion_id, category_id
            
        except Exception as e:
            print(f"❌ Error testing companion APIs: {e}")
            return False


async def test_chat_apis(companion_id: str):
    """Test chat functionality"""
    print("\n🧪 Testing Chat APIs...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Send message
            print("\n1️⃣ Sending chat message...")
            chat_data = {
                "companion_id": companion_id,
                "user_id": "test-user-123",
                "message": "Hello! Can you help me write a Python function?",
                "model_name": "gpt-4o-mini"
            }
            
            response = await client.post(
                f"{BASE_URL}/chat/send",
                json=chat_data
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                chat_response = response.json()
                print(f"✅ AI Response received (length: {len(chat_response['message'])} chars)")
                print(f"   Processing time: {chat_response['processing_time_ms']:.1f}ms")
                print(f"   Preview: {chat_response['message'][:100]}...")
            else:
                print(f"❌ Failed to send message: {response.text}")
                return False
            
            # Test 2: Get conversation history
            print("\n2️⃣ Fetching conversation history...")
            response = await client.get(
                f"{BASE_URL}/chat/history/{companion_id}",
                params={"user_id": "test-user-123"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                history = response.json()
                print(f"✅ Retrieved conversation history")
                print(f"   Total messages: {history['total_messages']}")
                print(f"   Companion: {history['companion_name']}")
                print(f"   Recent messages: {len(history['messages'])}")
            else:
                print(f"❌ Failed to fetch history: {response.text}")
                return False
            
            # Test 3: Memory statistics
            print("\n3️⃣ Getting memory statistics...")
            response = await client.get(
                f"{BASE_URL}/chat/memory/stats/{companion_id}",
                params={"user_id": "test-user-123"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Memory statistics retrieved")
                print(f"   Thread ID: {stats['thread_id']}")
                print(f"   Has distributed state: {stats['has_distributed_state']}")
            else:
                print(f"❌ Failed to get memory stats: {response.text}")
                return False
            
            # Test 4: Semantic search
            print("\n4️⃣ Testing semantic search...")
            search_data = {
                "query": "Python function",
                "k": 5
            }
            
            response = await client.post(
                f"{BASE_URL}/chat/semantic-search/{companion_id}",
                params={"user_id": "test-user-123", **search_data}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                search_results = response.json()
                print(f"✅ Semantic search completed")
                print(f"   Query: {search_results['query']}")
                print(f"   Results found: {search_results['total_results']}")
            else:
                print(f"❌ Failed semantic search: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing chat APIs: {e}")
            return False


async def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    
    import subprocess
    import time
    
    # Start server in background
    process = subprocess.Popen([
        "poetry", "run", "uvicorn", 
        "main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000",
        "--reload"
    ], cwd=".")
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    await asyncio.sleep(5)
    
    # Test if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print("✅ Server is running!")
                return process
    except:
        pass
    
    print("❌ Server failed to start")
    process.terminate()
    return None


async def main():
    """Run complete API test suite"""
    print("🧪 Sentient AI Backend API Test Suite")
    print("=" * 50)
    
    # Initialize database first
    print("\n📁 Initializing database...")
    from src.config.database import init_db
    await init_db()
    print("✅ Database initialized")
    
    # Start server
    server_process = await start_server()
    if not server_process:
        print("❌ Cannot start server, aborting tests")
        return
    
    try:
        # Test companion APIs
        companion_result = await test_companion_apis()
        if not companion_result:
            print("❌ Companion API tests failed")
            return
        
        companion_id, category_id = companion_result
        
        # Test chat APIs
        chat_result = await test_chat_apis(companion_id)
        if not chat_result:
            print("❌ Chat API tests failed")
            return
        
        print("\n🎉 ALL API TESTS PASSED!")
        print("✅ Companion CRUD operations working")
        print("✅ Chat functionality working")
        print("✅ Distributed memory system working")
        print("✅ Database persistence working")
        
        print(f"\n🔗 API Documentation: {BASE_URL}/docs")
        print(f"📊 Database file: {Path('sentient_ai.db').absolute()}")
        
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("\n🧹 Stopping server...")
        server_process.terminate()
        await asyncio.sleep(2)
        print("✅ Server stopped")


if __name__ == "__main__":
    asyncio.run(main()) 