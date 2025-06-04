"""
Sentient AI Backend - Main FastAPI Application
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.api.routes import chat, companion, auth, upload
from src.config.settings import get_settings
from src.config.database import init_db

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler"""
    # Startup
    print("🚀 Starting Sentient AI Backend...")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Sentient AI Backend...")

# Initialize FastAPI app
app = FastAPI(
    title="Sentient AI Backend",
    description="Python/LangGraph backend for AI Companions",
    version="0.1.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(companion.router, tags=["companions"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Sentient AI Backend is running",
        "version": "0.1.0",
        "status": "healthy",
        "docs": "/docs",
        "endpoints": {
            "companions": "/companions",
            "chat": "/chat", 
            "auth": "/api/auth"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": "operational",
        "features": [
            "Distributed Memory Management",
            "Character Agent System", 
            "SQLite Database",
            "LangGraph Integration"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 