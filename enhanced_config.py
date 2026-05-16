"""
Enhanced Chatbot Configuration
Supports OpenAI, LangChain, ChromaDB, PostgreSQL
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "NBKR Institute AI Chatbot Enhanced"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # or "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 500
    
    # LangChain
    LANGCHAIN_TRACING: bool = False
    LANGCHAIN_PROJECT: str = "nbkr-chatbot"
    
    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "nbkr_knowledge"
    
    # PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/nbkr_chatbot"
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Data Files
    FACULTY_DATA_FILE: str = "aids_faculty_data.json"
    TIMETABLE_DATA_FILE: str = "aids_timetable_data.json"
    NBKR_KB_FILE: str = "nbkr_knowledge_base.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
