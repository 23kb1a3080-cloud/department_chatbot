"""
SQLAlchemy models for College AI Chatbot System.
Defines all database tables and relationships.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Float,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from .base import Base, TimestampMixin


# Enums
class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    FACULTY = "faculty"
    STUDENT = "student"


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ChatSessionStatus(str, enum.Enum):
    """Chat session status enumeration."""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class DocumentStatus(str, enum.Enum):
    """Document processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channel enumeration."""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"


# Models
class Role(Base, TimestampMixin):
    """Role model for role-based access control."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    permissions = Column(JSONB, default=dict)  # Store permissions as JSON
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Role and status
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255))
    
    # Profile information
    department = Column(String(100))
    student_id = Column(String(50), index=True)  # For students
    faculty_id = Column(String(50), index=True)  # For faculty
    phone_number = Column(String(20))
    
    # Metadata
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Preferences
    preferences = Column(JSONB, default=dict)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploaded_by_user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Session(Base, TimestampMixin):
    """Session model for user authentication sessions."""
    
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Token information
    access_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, index=True)
    
    # Session details
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Client information
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_info = Column(JSONB)
    
    # Session metadata
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ChatSession(Base, TimestampMixin):
    """Chat session model for conversation management."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session details
    title = Column(String(255))
    status = Column(SQLEnum(ChatSessionStatus), default=ChatSessionStatus.ACTIVE, nullable=False)
    
    # Conversation context
    context = Column(JSONB, default=dict)  # Store conversation context
    meta_data = Column(JSONB, default=dict)  # Additional metadata
    
    # Session statistics
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime)
    
    # Archival
    archived_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ChatMessage(Base, TimestampMixin):
    """Chat message model for storing conversation messages."""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Message metadata
    tokens_used = Column(Integer)
    model_used = Column(String(100))
    response_time_ms = Column(Integer)
    
    # RAG information
    sources = Column(JSONB)  # Store source documents used for response
    confidence_score = Column(Float)
    
    # Feedback
    feedback_rating = Column(Integer)  # 1-5 rating
    feedback_comment = Column(Text)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.chat_session_id})>"


class Document(Base, TimestampMixin):
    """Document model for uploaded files and knowledge base."""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Document information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    file_type = Column(String(50))  # MIME type
    file_extension = Column(String(10))
    
    # Processing status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False, index=True)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_error = Column(Text)
    
    # Content
    extracted_text = Column(Text)
    text_length = Column(Integer)
    
    # Metadata
    title = Column(String(500))
    description = Column(Text)
    department = Column(String(100), index=True)
    category = Column(String(100), index=True)
    tags = Column(JSONB)  # Array of tags
    meta_data = Column(JSONB, default=dict)
    
    # Versioning
    version = Column(Integer, default=1)
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Upload information
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Vector database reference
    vector_ids = Column(JSONB)  # Store vector database IDs for chunks
    chunk_count = Column(Integer, default=0)
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    parent_document = relationship("Document", remote_side=[id])
    knowledge_base_entries = relationship("KnowledgeBase", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class KnowledgeBase(Base, TimestampMixin):
    """Knowledge base model for processed document chunks."""
    
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    
    # Chunk information
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_size = Column(Integer)
    
    # Vector information
    vector_id = Column(String(255), index=True)  # ID in vector database
    embedding_model = Column(String(100))
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    
    # Search optimization
    keywords = Column(JSONB)  # Extracted keywords
    summary = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="knowledge_base_entries")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class Notification(Base, TimestampMixin):
    """Notification model for user notifications."""
    
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), index=True)  # 'announcement', 'alert', 'reminder', etc.
    
    # Delivery
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    
    # Scheduling
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # Priority and expiry
    priority = Column(Integer, default=0)  # Higher number = higher priority
    expires_at = Column(DateTime)
    
    # Metadata
    metadata = Column(JSONB, default=dict)
    error_message = Column(Text)
    
    # Action
    action_url = Column(String(500))
    action_label = Column(String(100))
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.notification_type})>"


class AuditLog(Base, TimestampMixin):
    """Audit log model for security and compliance tracking."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # Event information
    event_type = Column(String(100), nullable=False, index=True)  # 'login', 'logout', 'access_denied', etc.
    event_category = Column(String(50), index=True)  # 'authentication', 'authorization', 'data_access', etc.
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    
    # Event details
    description = Column(Text)
    status = Column(String(20))  # 'success', 'failure', 'error'
    
    # Request information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(String(500))
    
    # Additional data
    metadata = Column(JSONB, default=dict)
    changes = Column(JSONB)  # Store before/after values for data changes
    
    # Security
    severity = Column(String(20))  # 'low', 'medium', 'high', 'critical'
    is_suspicious = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"


class SystemConfig(Base, TimestampMixin):
    """System configuration model for application settings."""
    
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration key-value
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    
    # Metadata
    description = Column(Text)
    category = Column(String(50), index=True)  # 'general', 'security', 'ai', 'notification', etc.
    data_type = Column(String(20))  # 'string', 'integer', 'boolean', 'json', etc.
    
    # Validation
    is_sensitive = Column(Boolean, default=False)  # Encrypt sensitive values
    is_editable = Column(Boolean, default=True)
    validation_rules = Column(JSONB)  # Store validation rules
    
    # Change tracking
    modified_by = Column(UUID(as_uuid=True))
    previous_value = Column(JSONB)
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, key={self.key})>"
