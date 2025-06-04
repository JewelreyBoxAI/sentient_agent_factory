#!/usr/bin/env python3
"""
Database Initialization Script for Sentient AI
Creates SQLite database and tables for prototype
"""
import asyncio
import os
import sys
from pathlib import Path

# Set environment variables for prototype
os.environ["OPENAI_API_KEY"] = "sk-test-key-placeholder"
os.environ["DEBUG"] = "true"

# Add src to path
sys.path.append("src")

async def main():
    """Initialize database and run basic tests"""
    try:
        print("🚀 Starting Database Initialization...")
        
        # Import components
        from src.config.database import init_db, get_db, Base, async_engine
        from src.models.companion import Companion, Category
        from src.models.message import Message, MessageRole
        from src.models.user import UserSubscription, UserApiLimit
        from sqlalchemy import text
        
        print("✅ Imports successful")
        
        # Initialize database
        print("\n🗄️ Initializing SQLite database...")
        await init_db()
        
        # Check if database file was created
        db_file = Path("sentient_ai.db")
        if db_file.exists():
            print(f"✅ Database file created: {db_file.absolute()}")
            print(f"📊 Database size: {db_file.stat().st_size} bytes")
        else:
            print("❌ Database file not found")
            return
        
        # Test database connection
        print("\n🔗 Testing database connection...")
        async with async_engine.begin() as conn:
            # Check tables exist
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result]
            print(f"✅ Tables created: {tables}")
        
        # Test basic CRUD operations
        print("\n📝 Testing CRUD operations...")
        
        # Get database session
        from src.config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            # Create test category first
            test_category = Category(name="Test Category")
            session.add(test_category)
            await session.commit()
            await session.refresh(test_category)
            
            print(f"✅ Created category: {test_category.name} (ID: {test_category.id})")
            
            # Create test companion with correct field names
            test_companion = Companion(
                user_id="test-user-123",
                user_name="Test User",
                name="Test Assistant",
                short_description="A helpful AI assistant for testing",
                character_description={"role": "assistant", "personality": "helpful"},
                category_id=test_category.id,
                src="https://example.com/avatar.png",
                humor=4,
                empathy=5,
                assertiveness=3,
                sarcasm=2
            )
            
            session.add(test_companion)
            await session.commit()
            await session.refresh(test_companion)
            
            print(f"✅ Created companion: {test_companion.name} (ID: {test_companion.id})")
            
            # Create test message
            test_message = Message(
                content="Hello, this is a test message!",
                role=MessageRole.USER,
                companion_id=test_companion.id,
                user_id="test-user-123"
            )
            
            session.add(test_message)
            await session.commit()
            await session.refresh(test_message)
            
            print(f"✅ Created message: {test_message.content[:50]}... (ID: {test_message.id})")
            
            # Create test user subscription
            test_subscription = UserSubscription(
                user_id="test-user-123",
                stripe_customer_id="cus_test_12345"
            )
            
            session.add(test_subscription)
            await session.commit()
            await session.refresh(test_subscription)
            
            print(f"✅ Created user subscription: {test_subscription.user_id} (ID: {test_subscription.id})")
            
            # Test query
            result = await session.execute(
                text("SELECT COUNT(*) FROM categories")
            )
            category_count = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM companions")
            )
            companion_count = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM messages")
            )
            message_count = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM user_subscriptions")
            )
            subscription_count = result.scalar()
            
            print(f"✅ Database stats: {category_count} categories, {companion_count} companions, {message_count} messages, {subscription_count} subscriptions")
        
        print("\n🎉 DATABASE INITIALIZATION COMPLETE!")
        print("🔗 Ready for Step 3: CRUD API development")
        print(f"📁 Database location: {db_file.absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ All systems ready for backend development!")
    else:
        print("\n❌ Setup failed - please check errors above")
        sys.exit(1) 