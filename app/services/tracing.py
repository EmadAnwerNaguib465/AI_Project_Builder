"""Optional LangSmith tracing configuration for the agent pipeline."""

import os
from typing import Any
from uuid import UUID

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_last_configuration: tuple[bool, bool, str, str] | None = None


def configure_langsmith() -> bool:
    """Configure LangSmith from application settings without exposing secrets."""
    global _last_configuration

    enabled = settings.langsmith_enabled
    configuration = (
        settings.langsmith_tracing,
        bool(settings.langsmith_api_key.strip()),
        settings.langsmith_project,
        settings.langsmith_endpoint,
    )

    os.environ["LANGSMITH_TRACING"] = "true" if enabled else "false"

    if enabled:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    else:
        os.environ.pop("LANGSMITH_API_KEY", None)
        os.environ.pop("LANGSMITH_PROJECT", None)
        os.environ.pop("LANGSMITH_ENDPOINT", None)

    if configuration != _last_configuration:
        if enabled:
            logger.info(
                "LangSmith tracing enabled for project '%s'",
                settings.langsmith_project,
            )
        elif settings.langsmith_tracing:
            logger.warning(
                "LangSmith tracing was requested but LANGSMITH_API_KEY is missing"
            )
        else:
            logger.debug("LangSmith tracing is disabled")
        _last_configuration = configuration

    return enabled


def pipeline_trace_config(run_id: UUID | None = None) -> dict[str, Any]:
    """Return stable labels and metadata for each pipeline trace."""
    config: dict[str, Any] = {
        "run_name": "AI Project Builder Pipeline",
        "tags": ["ai-project-builder", "langgraph"],
        "metadata": {
            "app_version": settings.app_version,
            "llm_model": settings.llm_model,
        },
    }
    if run_id is not None:
        config["run_id"] = run_id
    return config
