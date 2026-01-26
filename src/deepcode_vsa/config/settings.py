"""Settings configuration using Pydantic Settings.

Reference: .claude/skills/vsa-llm-config/SKILL.md
"""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelTier(str, Enum):
    """LLM model tiers for different task types."""
    
    FAST = "fast"        # Classification, GUT, simple tasks
    SMART = "smart"      # RCA, planning, analysis
    PREMIUM = "premium"  # Critical tasks, fallback
    CREATIVE = "creative"  # Reports, summaries


class GLPISettings(BaseSettings):
    """GLPI API configuration."""
    
    model_config = SettingsConfigDict(env_prefix="GLPI_")
    
    enabled: bool = True
    base_url: str = Field(default="", description="GLPI API base URL")
    app_token: str = Field(default="", description="GLPI App Token")
    user_token: str = Field(default="", description="GLPI User Token")


class ZabbixSettings(BaseSettings):
    """Zabbix API configuration."""
    
    model_config = SettingsConfigDict(env_prefix="ZABBIX_")
    
    enabled: bool = True
    base_url: str = Field(default="", description="Zabbix API URL")
    api_token: str = Field(default="", description="Zabbix API Token")


class LLMSettings(BaseSettings):
    """LLM configuration with hybrid model strategy."""
    
    model_config = SettingsConfigDict(env_prefix="LLM_")
    
    provider: str = "openrouter"
    api_key: str = Field(default="")
    
    # Fast model - classification, GUT (free/cheap)
    fast_model: str = "meta-llama/llama-3.3-70b-instruct"
    
    # Smart model - RCA, planning (cheap, quality)
    smart_model: str = "deepseek/deepseek-chat"
    
    # Premium model - fallback, critical tasks
    premium_model: str = "anthropic/claude-3.5-sonnet"
    
    # Creative model - reports, summaries
    creative_model: str = "minimax/minimax-m2-her"
    
    # Default tier
    default_tier: ModelTier = ModelTier.SMART


class DatabaseSettings(BaseSettings):
    """PostgreSQL configuration for LangGraph checkpointer."""
    
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="deepcode_vsa")
    user: str = Field(default="postgres")
    password: str = Field(default="")
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application
    app_name: str = "DeepCode VSA"
    debug: bool = False
    dry_run: bool = True  # Safe by default
    
    # Sub-settings
    glpi: GLPISettings = Field(default_factory=GLPISettings)
    zabbix: ZabbixSettings = Field(default_factory=ZabbixSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
