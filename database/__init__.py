"""
Database package for College AI Chatbot System.
Provides database models, connection management, and utilities.
"""

from .connection import engine, SessionLocal, get_db, init_db
from .models import (
    User,
    Role,
    Session,
    ChatMessage,
    ChatSession,
    Document,
    KnowledgeBase,
    Notification,
    AuditLog,
    SystemConfig,
)

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "User",
    "Role",
    "Session",
    "ChatMessage",
    "ChatSession",
    "Document",
    "KnowledgeBase",
    "Notification",
    "AuditLog",
    "SystemConfig",
]
