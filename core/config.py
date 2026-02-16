"""Settings configuration using Pydantic Settings.

Reference: .claude/skills/vsa-llm-config/SKILL.md
"""

from enum import Enum
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelTier(str, Enum):
    """LLM model tiers for different task types."""

    FAST = "fast"  # Classification, GUT, simple tasks
    SMART = "smart"  # RCA, planning, analysis
    PREMIUM = "premium"  # Critical tasks, fallback
    CREATIVE = "creative"  # Reports, summaries


class GLPISettings(BaseSettings):
    """GLPI API configuration."""

    model_config = SettingsConfigDict(env_prefix="GLPI_")

    enabled: bool = True
    base_url: str = Field(default="", description="GLPI API base URL")
    app_token: str = Field(default="", description="GLPI App Token")
    user_token: str = Field(default="", description="GLPI User Token (optional)")
    username: str = Field(default="", description="GLPI Username for Basic Auth")
    password: str = Field(default="", description="GLPI Password for Basic Auth")


class ZabbixSettings(BaseSettings):
    """Zabbix API configuration."""

    model_config = SettingsConfigDict(env_prefix="ZABBIX_")

    enabled: bool = True
    base_url: str = Field(default="", description="Zabbix API URL")
    api_token: str = Field(default="", description="Zabbix API Token")


class LinearSettings(BaseSettings):
    """Linear.app API configuration."""

    model_config = SettingsConfigDict(env_prefix="LINEAR_")

    enabled: bool = True
    api_key: str = Field(default="", description="Linear API Key")


class LLMSettings(BaseSettings):
    """LLM configuration with hybrid model strategy."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: str = "openrouter"
    api_key: str = Field(
        default="", validation_alias=AliasChoices("LLM_API_KEY", "OPENROUTER_API_KEY")
    )

    # Fast model - classification, GUT (free/cheap)
    fast_model: str = "meta-llama/llama-3.3-70b-instruct"

    # Smart model - RCA, planning (cheap, quality)
    smart_model: str = "deepseek/deepseek-chat"

    # Premium model - fallback, critical tasks
    premium_model: str = "anthropic/claude-3.5-sonnet"

    # Creative model - reports, summaries
    creative_model: str = "minimax/minimax-m2-her"

    # Vision model - multimodal (images)
    vision_model: str = "openai/gpt-4o-mini"

    # Default tier
    default_tier: ModelTier = ModelTier.SMART


class DatabaseSettings(BaseSettings):
    """PostgreSQL configuration for LangGraph checkpointer."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(
        default="deepcode_vsa", validation_alias=AliasChoices("DB_DATABASE", "DB_NAME")
    )
    user: str = Field(default="postgres")
    password: str = Field(default="")

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        from urllib.parse import quote_plus

        safe_user = quote_plus(self.user)
        safe_password = quote_plus(self.password)
        return f"postgresql://{safe_user}:{safe_password}@{self.host}:{self.port}/{self.database}"

    @property
    def connection_string_sqlalchemy(self) -> str:
        """Get PostgreSQL connection string for SQLAlchemy (APScheduler compatibility).
        
        Uses postgresql+psycopg dialect to ensure compatibility with psycopg3.
        """
        from urllib.parse import quote_plus
        safe_user = quote_plus(self.user)
        safe_password = quote_plus(self.password)
        return f"postgresql+psycopg://{safe_user}:{safe_password}@{self.host}:{self.port}/{self.database}"


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "DeepCode VSA"
    debug: bool = False
    dry_run: bool = True  # Safe by default

    # Modelo padrão para tarefas agendadas
    default_model_name: str = Field(
        default="z-ai/glm-4.5-air:free", validation_alias=AliasChoices("DEFAULT_MODEL_NAME")
    )

    # Sub-settings
    glpi: GLPISettings = Field(default_factory=GLPISettings)
    zabbix: ZabbixSettings = Field(default_factory=ZabbixSettings)
    linear: LinearSettings = Field(default_factory=LinearSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    # File storage (MinIO)
    minio_endpoint: str = Field(default="", validation_alias=AliasChoices("MINIO_ENDPOINT"))
    minio_public_endpoint: str = Field(
        default="", validation_alias=AliasChoices("MINIO_PUBLIC_ENDPOINT")
    )
    minio_access_key: str = Field(default="", validation_alias=AliasChoices("MINIO_ACCESS_KEY"))
    minio_secret_key: str = Field(default="", validation_alias=AliasChoices("MINIO_SECRET_KEY"))
    minio_bucket: str = Field(default="vsa-uploads", validation_alias=AliasChoices("MINIO_BUCKET"))
    files_max_size_mb: int = Field(default=4, validation_alias=AliasChoices("FILES_MAX_SIZE_MB"))
    signed_url_ttl_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices("SIGNED_URL_TTL_SECONDS"),
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    from dotenv import load_dotenv

    load_dotenv()
    return Settings()
