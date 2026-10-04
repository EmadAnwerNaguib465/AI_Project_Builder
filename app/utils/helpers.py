"""
app/utils/helpers.py

Shared utility functions used across multiple modules.
Keeps common operations DRY and testable.
"""

import json
import re
import time
from datetime import datetime
from typing import Any, Optional
from pathlib import Path


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncates a string to max_length characters.

    Args:
        text: The input string.
        max_length: Maximum allowed length.
        suffix: Appended when text is truncated.

    Returns:
        Truncated string, or original if within limit.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_text(text: str) -> str:
    """
    Removes excessive whitespace and normalizes line breaks.

    Args:
        text: Raw input string.

    Returns:
        Cleaned string.
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple blank lines into a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace
    return text.strip()


def safe_json_parse(text: str) -> Optional[dict]:
    """
    Attempts to parse a JSON string. Returns None on failure instead of raising.

    Args:
        text: String that may contain JSON.

    Returns:
        Parsed dict, or None if parsing fails.
    """
    try:
        # Strip markdown code fences if present (LLMs often wrap JSON in ```json)
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return None


def format_sources(sources: list[str]) -> str:
    """
    Formats a list of source URLs/references into a readable numbered list.

    Args:
        sources: List of source strings.

    Returns:
        Formatted string with numbered entries.
    """
    if not sources:
        return "No sources available."
    unique = list(dict.fromkeys(sources))  # deduplicate while preserving order
    return "\n".join(f"{i + 1}. {src}" for i, src in enumerate(unique))


def timestamp_str() -> str:
    """Returns the current UTC timestamp as an ISO-format string."""
    return datetime.utcnow().isoformat() + "Z"


def ensure_dir(path: Path) -> Path:
    """
    Creates a directory (and all parents) if it does not exist.

    Args:
        path: Directory path to create.

    Returns:
        The same path, for chaining.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def retry(func, max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Simple synchronous retry decorator-style helper.

    Args:
        func: Callable to execute.
        max_attempts: Maximum number of attempts.
        delay: Seconds to wait between attempts.
        exceptions: Exception types to catch and retry on.

    Returns:
        Result of func on success.

    Raises:
        Last caught exception if all attempts fail.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except exceptions as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(delay)
    raise last_error


def flatten_list(nested: list[Any]) -> list[Any]:
    """Flattens one level of nesting in a list."""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def merge_dicts(*dicts: dict) -> dict:
    """
    Merges multiple dicts left-to-right.
    Later dicts override earlier keys.

    Args:
        *dicts: Dictionaries to merge.

    Returns:
        Single merged dictionary.
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result
