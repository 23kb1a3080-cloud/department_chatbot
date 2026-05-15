"""
Configuration management for College AI Chatbot System.
Loads environment variables and provides configuration objects for all services.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Main application settings loaded from environment variables."""
    
    # Application Configuration
    app_name: str = Field(default="College AI Chatbot System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    
    # Database Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="college_chatbot", env="POSTGRES_DB")
    postgres_user: str = Field(default="chatbot_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="changeme", env="POSTGRES_PASSWORD")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, env="DB_MAX_OVERFLOW")
    
    @validator("database_url", pre=True, always=True)
    def assemble_db_url(cls, v, values):
        """Construct database URL if not provided."""
        if v:
            return v
        return (
            f"postgresql://{values.get('postgres_user')}:"
            f"{values.get('postgres_password')}@"
            f"{values.get('postgres_host')}:"
            f"{values.get('postgres_port')}/"
            f"{values.get('postgres_db')}"
        )
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_pool_size: int = Field(default=10, env="REDIS_POOL_SIZE")
    
    @validator("redis_url", pre=True, always=True)
    def assemble_redis_url(cls, v, values):
        """Construct Redis URL if not provided."""
        if v:
            return v
        password = values.get('redis_password')
        if password:
            return (
                f"redis://:{password}@{values.get('redis_host')}:"
                f"{values.get('redis_port')}/{values.get('redis_db')}"
            )
        return (
            f"redis://{values.get('redis_host')}:"
            f"{values.get('redis_port')}/{values.get('redis_db')}"
        )
    
    # Vector Database Configuration
    vector_db_type: str = Field(default="chromadb", env="VECTOR_DB_TYPE")
    vector_db_path: str = Field(default="./chroma_db", env="VECTOR_DB_PATH")
    vector_db_collection: str = Field(default="documents", env="VECTOR_DB_COLLECTION")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")
    
    # Authentication Configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        env="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    mfa_enabled: bool = Field(default=False, env="MFA_ENABLED")
    
    # Session Configuration
    session_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    max_concurrent_sessions: int = Field(default=5, env="MAX_CONCURRENT_SESSIONS")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # File Upload Configuration
    max_upload_size_mb: int = Field(default=50, env="MAX_UPLOAD_SIZE_MB")
    allowed_extensions: str = Field(
        default="pdf,docx,doc,xlsx,xls,txt,png,jpg,jpeg",
        env="ALLOWED_EXTENSIONS"
    )
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    temp_dir: str = Field(default="./temp_files", env="TEMP_DIR")
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Return allowed extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    # OCR Configuration
    tesseract_path: str = Field(default="/usr/bin/tesseract", env="TESSERACT_PATH")
    ocr_language: str = Field(default="eng", env="OCR_LANGUAGE")
    
    # AI/LLM Configuration
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # RAG Configuration
    rag_top_k: int = Field(default=5, env="RAG_TOP_K")
    rag_similarity_threshold: float = Field(default=0.7, env="RAG_SIMILARITY_THRESHOLD")
    rag_chunk_size: int = Field(default=500, env="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=50, env="RAG_CHUNK_OVERLAP")
    
    # External System Integration
    erp_api_url: Optional[str] = Field(default=None, env="ERP_API_URL")
    erp_api_key: Optional[str] = Field(default=None, env="ERP_API_KEY")
    notice_board_api_url: Optional[str] = Field(default=None, env="NOTICE_BOARD_API_URL")
    notice_board_api_key: Optional[str] = Field(default=None, env="NOTICE_BOARD_API_KEY")
    attendance_api_url: Optional[str] = Field(default=None, env="ATTENDANCE_API_URL")
    attendance_api_key: Optional[str] = Field(default=None, env="ATTENDANCE_API_KEY")
    library_api_url: Optional[str] = Field(default=None, env="LIBRARY_API_URL")
    library_api_key: Optional[str] = Field(default=None, env="LIBRARY_API_KEY")
    calendar_api_url: Optional[str] = Field(default=None, env="CALENDAR_API_URL")
    calendar_api_key: Optional[str] = Field(default=None, env="CALENDAR_API_KEY")
    
    # WebSocket Configuration
    ws_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    ws_max_connections: int = Field(default=1000, env="WS_MAX_CONNECTIONS")
    
    # Notification Configuration
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")
    sms_provider: str = Field(default="twilio", env="SMS_PROVIDER")
    sms_account_sid: Optional[str] = Field(default=None, env="SMS_ACCOUNT_SID")
    sms_auth_token: Optional[str] = Field(default=None, env="SMS_AUTH_TOKEN")
    sms_from_number: Optional[str] = Field(default=None, env="SMS_FROM_NUMBER")
    
    # Celery Configuration
    celery_broker_url: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    
    @validator("celery_broker_url", pre=True, always=True)
    def assemble_celery_broker(cls, v, values):
        """Construct Celery broker URL if not provided."""
        if v:
            return v
        return f"redis://{values.get('redis_host')}:{values.get('redis_port')}/1"
    
    @validator("celery_result_backend", pre=True, always=True)
    def assemble_celery_backend(cls, v, values):
        """Construct Celery result backend URL if not provided."""
        if v:
            return v
        return f"redis://{values.get('redis_host')}:{values.get('redis_port')}/2"
    
    # Monitoring and Logging
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3000, env="GRAFANA_PORT")
    elasticsearch_url: Optional[str] = Field(default=None, env="ELASTICSEARCH_URL")
    kibana_url: Optional[str] = Field(default=None, env="KIBANA_URL")
    
    # Security
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        env="CORS_ORIGINS"
    )
    allowed_hosts: str = Field(default="localhost,127.0.0.1", env="ALLOWED_HOSTS")
    encryption_key: str = Field(
        default="your-encryption-key-32-chars-min",
        env="ENCRYPTION_KEY"
    )
    security_audit_enabled: bool = Field(default=True, env="SECURITY_AUDIT_ENABLED")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Return allowed hosts as a list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]
    
    # Kubernetes Configuration
    k8s_namespace: str = Field(default="chatbot-system", env="K8S_NAMESPACE")
    k8s_replicas: int = Field(default=3, env="K8S_REPLICAS")
    k8s_cpu_request: str = Field(default="500m", env="K8S_CPU_REQUEST")
    k8s_cpu_limit: str = Field(default="1000m", env="K8S_CPU_LIMIT")
    k8s_memory_request: str = Field(default="512Mi", env="K8S_MEMORY_REQUEST")
    k8s_memory_limit: str = Field(default="1Gi", env="K8S_MEMORY_LIMIT")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
