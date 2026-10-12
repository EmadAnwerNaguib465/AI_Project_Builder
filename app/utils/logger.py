"""
app/utils/logger.py

Centralized structured logging for Planorai.
Provides a single `get_logger(name)` factory used by all modules.
Logs agent lifecycle events, tool calls, routing decisions, and errors.
Never logs API keys or sensitive data.
"""

import logging
import sys
from typing import Optional


# ANSI color codes for console output (Windows-safe via colorama if needed)
_COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    """Adds color to log level names in console output."""

    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
    DATE_FORMAT = "%H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, _COLORS["RESET"])
        reset = _COLORS["RESET"]
        record.levelname = f"{color}{record.levelname}{reset}"
        formatter = logging.Formatter(self.FORMAT, datefmt=self.DATE_FORMAT)
        return formatter.format(record)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Returns a named logger configured for this application.

    Usage:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Agent started")

    Args:
        name: Logger name, typically __name__ of the calling module.
        level: Optional log level override (e.g. "DEBUG"). If not provided,
               falls back to the LOG_LEVEL environment variable or INFO.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Determine log level
    if level is None:
        try:
            from app.config.settings import settings
            level = settings.log_level
        except Exception:
            level = "INFO"

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    # Prevent propagation to root logger (avoids duplicate output)
    logger.propagate = False

    return logger


# --- Convenience logging functions for agent lifecycle events ---

def log_agent_start(logger: logging.Logger, agent_name: str) -> None:
    """Log when an agent begins execution."""
    logger.info(f"[START] {agent_name}")


def log_agent_complete(logger: logging.Logger, agent_name: str) -> None:
    """Log when an agent finishes successfully."""
    logger.info(f"[DONE]  {agent_name}")


def log_tool_call(logger: logging.Logger, tool_name: str, query: str) -> None:
    """Log a tool invocation (without sensitive parameters)."""
    # Truncate long queries in logs
    truncated = query[:100] + "..." if len(query) > 100 else query
    logger.info(f"[TOOL]  {tool_name} | query='{truncated}'")


def log_routing(logger: logging.Logger, from_node: str, to_node: str, reason: str = "") -> None:
    """Log a graph routing decision."""
    msg = f"[->]    {from_node} -> {to_node}"
    if reason:
        msg += f" ({reason})"
    logger.info(msg)


def log_critic_result(
    logger: logging.Logger,
    status: str,
    severity: str,
    revision_count: int,
) -> None:
    """Log the critic agent's decision."""
    tag = "[PASS]" if status == "PASS" else "[REVISE]"
    logger.info(
        f"{tag} status={status} | severity={severity} | revision={revision_count}"
    )


def log_error(logger: logging.Logger, agent_name: str, error: Exception) -> None:
    """Log an agent error with traceback."""
    logger.error(f"[ERR]   {agent_name}: {type(error).__name__}: {error}", exc_info=True)
