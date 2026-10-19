"""Talks to any OpenAI-compatible chat API. Keys and URLs come from settings (.env)."""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base class. `message` is always safe to show to the user."""

    status_code = 502
    message = "The AI service had a problem. Please try again."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message


class LLMConfigError(LLMError):
    status_code = 503
    message = "The AI service is not configured. Ask the administrator to set LLM_API_KEY."


class LLMRateLimitError(LLMError):
    status_code = 429
    message = "The AI service is busy (rate limit reached). Please wait a moment and try again."


class LLMTimeoutError(LLMError):
    status_code = 504
    message = "The AI service took too long to respond. Please try again."


def _get_client():
    if not settings.LLM_API_KEY:
        raise LLMConfigError()
    from openai import OpenAI

    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL or None,
        timeout=settings.LLM_TIMEOUT_SECONDS,
        max_retries=1,
    )


def generate_answer(messages: list[dict]) -> str:
    """Send chat messages to the LLM and return the answer text."""
    import openai

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
    except openai.RateLimitError as exc:
        logger.warning("LLM rate limit: %s", exc)
        raise LLMRateLimitError() from exc
    except openai.APITimeoutError as exc:
        logger.warning("LLM timeout: %s", exc)
        raise LLMTimeoutError() from exc
    except openai.AuthenticationError as exc:
        logger.error("LLM authentication failed - check LLM_API_KEY")
        raise LLMConfigError("The AI service rejected the API key. Check LLM_API_KEY.") from exc
    except openai.APIError as exc:  # includes connection errors
        logger.error("LLM API error: %s", exc)
        raise LLMError() from exc

    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        raise LLMError("The AI service returned an empty answer. Please try again.")
    return answer
