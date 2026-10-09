"""
app/config/settings.py

Centralized application settings loaded from environment variables.
Uses pydantic-settings for type-safe configuration with .env support.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


# Root of the project (two levels up from this file: app/config/settings.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    All application settings are loaded from environment variables.
    Falls back to defaults where applicable.
    Raises a clear error on startup if required keys are missing.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- API Keys ---
    google_api_key: str = Field(default="", description="Google Gemini API key")
    openai_api_key: str = Field(default="", description="OpenAI API key for embeddings")
    tavily_api_key: str = Field(default="", description="Tavily web search API key")

    # --- LLM Configuration ---
    llm_model: str = Field(default="gemini-3.5-flash-lite", description="Primary LLM model name")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=8192, gt=0)
    llm_max_attempts: int = Field(default=4, ge=1, le=6)

    # --- Embedding Configuration ---
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_provider: str = Field(default="openai")

    # --- RAG Configuration ---
    chroma_persist_dir: str = Field(default="./data/chroma")
    knowledge_base_dir: str = Field(default="./data/knowledge_base")
    rag_top_k: int = Field(default=5, gt=0)
    chunk_size: int = Field(default=1000, gt=0)
    chunk_overlap: int = Field(default=200, ge=0)

    # --- Graph Configuration ---
    max_revisions: int = Field(default=2, ge=0)

    # --- Application ---
    app_name: str = Field(default="AI Project Builder")
    app_version: str = Field(default="1.0.0")
    log_level: str = Field(default="INFO")

    @property
    def chroma_persist_path(self) -> Path:
        """Resolved absolute path to the ChromaDB directory."""
        p = Path(self.chroma_persist_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def knowledge_base_path(self) -> Path:
        """Resolved absolute path to the knowledge base directory."""
        p = Path(self.knowledge_base_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p

    def validate_llm_keys(self) -> None:
        """
        Raises ValueError if the required API keys for the chosen providers
        are missing. Call this at application startup.
        """
        errors = []

        if not self.google_api_key:
            errors.append(
                "GOOGLE_API_KEY is not set. Required for the Gemini LLM.\n"
                "  → Get a free key at: https://aistudio.google.com/app/apikey"
            )

        if self.embedding_provider == "openai" and not self.openai_api_key:
            errors.append(
                "OPENAI_API_KEY is not set. Required for OpenAI embeddings.\n"
                "  → Get a key at: https://platform.openai.com/api-keys"
            )

        if not self.tavily_api_key:
            errors.append(
                "TAVILY_API_KEY is not set. Web search tool will be disabled.\n"
                "  → Get a free key at: https://app.tavily.com\n"
                "  (Non-fatal — the Research Agent will skip web search.)"
            )

        # Only raise on hard failures (missing LLM key)
        hard_errors = [e for e in errors if "GOOGLE_API_KEY" in e or "OPENAI_API_KEY" in e]
        if hard_errors:
            raise ValueError(
                "Missing required API keys:\n\n"
                + "\n\n".join(hard_errors)
                + "\n\nPlease copy .env.example to .env and fill in your keys."
            )

        # Soft warnings are handled by the logger (imported lazily to avoid circular import)
        return errors  # return all errors so caller can log warnings


# Singleton instance — import this throughout the application
settings = Settings()
