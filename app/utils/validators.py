"""
app/utils/validators.py

Input validation functions used at graph entry points and in the UI.
Keeps validation logic centralized and testable.
"""

import re
from typing import Optional


# --- Constants ---
MIN_IDEA_LENGTH = 20       # characters
MAX_IDEA_LENGTH = 2000     # characters
MIN_IDEA_WORDS = 5         # words


class ValidationError(ValueError):
    """Raised when user input fails validation."""
    pass


def validate_user_idea(idea: str) -> str:
    """
    Validates the raw project idea string submitted by the user.

    Rules:
    - Must not be empty or whitespace-only.
    - Must be at least MIN_IDEA_LENGTH characters long.
    - Must not exceed MAX_IDEA_LENGTH characters.
    - Must contain at least MIN_IDEA_WORDS words.
    - Must not be a generic placeholder.

    Args:
        idea: Raw string from the user input field.

    Returns:
        Cleaned (stripped) idea string if valid.

    Raises:
        ValidationError: With a user-readable message describing the problem.
    """
    if not idea or not idea.strip():
        raise ValidationError(
            "Project idea cannot be empty. "
            "Please describe your AI project idea in a few sentences."
        )

    cleaned = idea.strip()

    if len(cleaned) < MIN_IDEA_LENGTH:
        raise ValidationError(
            f"Project idea is too short ({len(cleaned)} chars). "
            f"Please provide at least {MIN_IDEA_LENGTH} characters. "
            "Example: 'Build a computer vision system to detect defects in manufacturing.'"
        )

    if len(cleaned) > MAX_IDEA_LENGTH:
        raise ValidationError(
            f"Project idea is too long ({len(cleaned)} chars). "
            f"Please keep it under {MAX_IDEA_LENGTH} characters."
        )

    word_count = len(cleaned.split())
    if word_count < MIN_IDEA_WORDS:
        raise ValidationError(
            f"Project idea has too few words ({word_count} words). "
            f"Please use at least {MIN_IDEA_WORDS} words to describe your project."
        )

    # Reject generic placeholders
    placeholders = {"test", "hello", "hi", "abc", "example", "sample", "demo", "placeholder"}
    if cleaned.lower() in placeholders:
        raise ValidationError(
            "Please enter a real project idea, not a placeholder. "
            "Example: 'Build an NLP system for sentiment analysis of customer reviews.'"
        )

    return cleaned


def validate_revision_count(revision_count: int, max_revisions: int) -> bool:
    """
    Checks whether another revision cycle is allowed.

    Args:
        revision_count: Current number of completed revisions.
        max_revisions: Maximum allowed revisions from settings.

    Returns:
        True if revision is allowed, False if limit is reached.
    """
    return revision_count < max_revisions


def validate_api_key_format(key: str, provider: str) -> Optional[str]:
    """
    Performs a basic format check on an API key.
    Does NOT make a network call — just checks length/prefix.

    Args:
        key: The API key string.
        provider: One of "google", "openai", "tavily".

    Returns:
        None if valid, or an error message string if invalid.
    """
    if not key or not key.strip():
        return f"{provider.upper()} API key is empty."

    key = key.strip()

    if provider == "openai":
        if not key.startswith("sk-"):
            return "OpenAI API key should start with 'sk-'."
        if len(key) < 20:
            return "OpenAI API key seems too short."

    elif provider == "google":
        if len(key) < 10:
            return "Google API key seems too short."

    elif provider == "tavily":
        if not key.startswith("tvly-"):
            return "Tavily API key should start with 'tvly-'."

    return None  # valid


def validate_document_path(path: str) -> Optional[str]:
    """
    Validates that a document path has a supported extension.

    Supported: .pdf, .txt, .md, .docx

    Args:
        path: File path string.

    Returns:
        None if valid, or error message string.
    """
    supported = {".pdf", ".txt", ".md", ".docx"}
    from pathlib import Path
    suffix = Path(path).suffix.lower()
    if suffix not in supported:
        return (
            f"Unsupported file type '{suffix}'. "
            f"Supported types: {', '.join(sorted(supported))}"
        )
    return None
