"""
app/services/llm_service.py

Central LLM abstraction for the AI Project Builder.
All agents use this service — never instantiate LLMs directly in agent files.

Primary provider: Google Gemini (gemini-2.0-flash)
Structured output: via langchain's .with_structured_output() — uses Gemini function calling.

Usage:
    from app.services.llm_service import LLMService
    llm_service = LLMService()

    # Plain text response
    text = llm_service.invoke("What is machine learning?")

    # Structured Pydantic response
    from app.models.research_models import ResearchResult
    result: ResearchResult = llm_service.invoke_structured("...", ResearchResult)
"""

import os
from time import sleep
from pathlib import Path
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from google.genai.errors import APIError
from httpx import TimeoutException, TransportError
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from app.config.settings import settings
from app.utils.logger import get_logger, log_error

logger = get_logger(__name__)

# Generic type for structured output
T = TypeVar("T", bound=BaseModel)

# Directory containing prompt .txt files
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def is_transient_llm_error(error: BaseException) -> bool:
    return (
        isinstance(error, APIError) and error.code in {500, 502, 503, 504}
    ) or isinstance(error, (TimeoutException, TransportError))


def llm_failure_message(error: Exception, context: str) -> str:
    if is_transient_llm_error(error):
        return (
            f"The AI provider is temporarily unavailable after {settings.llm_max_attempts} attempts. "
            "Please wait a minute and try again."
        )
    return f"{context}: {type(error).__name__}: {error}"


class LLMService:
    """
    Wrapper around the Gemini LLM for use by all agents.

    Provides:
    - invoke()           → plain text response
    - invoke_structured()→ Pydantic model response (via function calling)
    - load_prompt()      → read a prompt file by name
    - get_structured_llm() → raw structured Runnable for agent use
    """

    def __init__(self) -> None:
        self._llm: Optional[ChatGoogleGenerativeAI] = None
        self._initialized = False

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """
        Lazily initializes the Gemini LLM.
        Deferred so that missing API keys only fail at call time, not import time.
        """
        if self._llm is None:
            if not settings.google_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY is not set in your .env file.\n"
                    "Get a free key at: https://aistudio.google.com/app/apikey"
                )

            # Set the API key in the environment (required by langchain-google-genai)
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key

            self._llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_output_tokens=settings.llm_max_tokens,
                thinking_level="low" if settings.llm_model.startswith("gemini-3") else None,
                timeout=120,
                # One SDK attempt; the service owns the bounded retry policy.
                max_retries=1,
                convert_system_message_to_human=False,
            )
            logger.info(f"LLM initialized: {settings.llm_model}")

        return self._llm

    def get_structured_llm(self, output_model: Type[T]) -> Runnable:
        """
        Returns a Runnable that forces Gemini to respond with a valid
        instance of `output_model` via function calling.

        Args:
            output_model: A Pydantic BaseModel class.

        Returns:
            Langchain Runnable: invoke it with a string or message list
            and it returns a validated instance of output_model.
        """
        llm = self._get_llm()
        return llm.with_structured_output(output_model)

    @staticmethod
    def _invoke_with_retry(runnable: Runnable, messages: list):
        def log_retry(state):
            logger.warning(
                "Transient LLM failure (%s), attempt %s/%s; retrying in %.1fs",
                type(state.outcome.exception()).__name__,
                state.attempt_number,
                settings.llm_max_attempts,
                state.next_action.sleep,
            )

        # Retry only the failed call, retaining the agent's prompt and upstream work.
        retry = Retrying(
            retry=retry_if_exception(is_transient_llm_error),
            stop=stop_after_attempt(settings.llm_max_attempts),
            wait=wait_exponential_jitter(initial=2, max=20, jitter=1),
            sleep=sleep,
            before_sleep=log_retry,
            reraise=True,
        )
        return retry(runnable.invoke, messages)

    def invoke(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Invokes the LLM and returns a plain text string response.

        Args:
            user_prompt: The human/user message content.
            system_prompt: Optional system instruction prepended to the conversation.

        Returns:
            Plain text response string.

        Raises:
            RuntimeError: On LLM call failure after logging the error.
        """
        try:
            llm = self._get_llm()

            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=user_prompt))

            response = self._invoke_with_retry(llm, messages)
            return str(response.text)

        except Exception as e:
            log_error(logger, "LLMService.invoke", e)
            raise RuntimeError(llm_failure_message(e, "LLM call failed")) from e

    def invoke_structured(
        self,
        user_prompt: str,
        output_model: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        """
        Invokes the LLM and returns a validated Pydantic model instance.
        Uses Gemini's native function calling for reliable structured output.

        Args:
            user_prompt: The human/user message content.
            output_model: The Pydantic class to parse the response into.
            system_prompt: Optional system instruction.

        Returns:
            An instance of output_model.

        Raises:
            RuntimeError: If the LLM call or Pydantic validation fails.
        """
        try:
            structured_llm = self.get_structured_llm(output_model)

            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=user_prompt))

            result = self._invoke_with_retry(structured_llm, messages)

            # Validate the returned object is actually the right type
            if not isinstance(result, output_model):
                raise ValueError(
                    f"LLM returned {type(result).__name__}, expected {output_model.__name__}"
                )

            return result

        except Exception as e:
            log_error(logger, f"LLMService.invoke_structured[{output_model.__name__}]", e)
            raise RuntimeError(llm_failure_message(
                e, f"Structured LLM call failed for {output_model.__name__}"
            )) from e

    @staticmethod
    def load_prompt(prompt_name: str) -> str:
        """
        Reads a prompt template from the app/prompts/ directory.

        Args:
            prompt_name: Filename without extension (e.g. "supervisor").

        Returns:
            The prompt file content as a string.

        Raises:
            FileNotFoundError: If the prompt file does not exist.
        """
        prompt_path = PROMPTS_DIR / f"{prompt_name}.txt"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Expected file: app/prompts/{prompt_name}.txt"
            )

        content = prompt_path.read_text(encoding="utf-8").strip()

        if not content:
            raise ValueError(
                f"Prompt file is empty: app/prompts/{prompt_name}.txt"
            )

        return content

    @staticmethod
    def format_prompt(template: str, **kwargs: str) -> str:
        """
        Substitutes {placeholders} in a prompt template with provided values.

        Args:
            template: Prompt string with {placeholder} markers.
            **kwargs: Key-value pairs for substitution.

        Returns:
            Formatted prompt string.

        Example:
            formatted = LLMService.format_prompt(template, user_idea="Build a chatbot")
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing prompt placeholder: {e}") from e


# Module-level singleton — import this in agents instead of instantiating directly
llm_service = LLMService()
