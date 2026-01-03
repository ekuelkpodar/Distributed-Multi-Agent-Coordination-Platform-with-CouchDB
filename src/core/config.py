"""
Core configuration management for the distributed agent platform.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # CouchDB Settings
    couchdb_url: str = Field(default="http://localhost:5984", description="CouchDB URL")
    couchdb_user: str = Field(default="admin", description="CouchDB username")
    couchdb_password: str = Field(default="password", description="CouchDB password")
    couchdb_database: str = Field(default="agent_coordination", description="Main database name")
    
    # Redis Settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    
    # LLM Settings
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    langsmith_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    
    # Agent Settings
    agent_heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")
    agent_failure_threshold: int = Field(default=90, description="Agent failure threshold in seconds")
    max_concurrent_tasks: int = Field(default=5, description="Max concurrent tasks per agent")
    
    # Monitoring Settings
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    grafana_port: int = Field(default=3000, description="Grafana port")
    
    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # Replication Settings
    replication_continuous: bool = Field(default=True, description="Enable continuous replication")
    replication_retry_delay: int = Field(default=5, description="Replication retry delay in seconds")
    
    # Task Queue Settings
    task_queue_poll_interval: int = Field(default=5, description="Task queue polling interval")
    task_retry_max_attempts: int = Field(default=3, description="Max task retry attempts")
    task_retry_backoff_factor: int = Field(default=2, description="Exponential backoff factor")


# Global settings instance
settings = Settings()
