"""Tests for the real llm_service code, using a fake OpenAI client (no network, no cost)."""
from types import SimpleNamespace

import httpx
import openai
import pytest

from rag import llm_service


def fake_client(result=None, error=None):
    def create(**kwargs):
        if error:
            raise error
        return result

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def _response(status):
    return httpx.Response(status, request=httpx.Request("POST", "http://llm.test/v1/chat/completions"))


def completion(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def test_returns_trimmed_answer(monkeypatch):
    monkeypatch.setattr(llm_service, "_get_client", lambda: fake_client(completion("  Hello (page 1)  ")))
    assert llm_service.generate_answer([{"role": "user", "content": "hi"}]) == "Hello (page 1)"


def test_missing_key_raises_config_error(settings):
    settings.LLM_API_KEY = ""
    with pytest.raises(llm_service.LLMConfigError):
        llm_service.generate_answer([])


@pytest.mark.parametrize(
    "error,expected",
    [
        (openai.RateLimitError("limit", response=_response(429), body=None), llm_service.LLMRateLimitError),
        (openai.APITimeoutError(request=httpx.Request("POST", "http://x")), llm_service.LLMTimeoutError),
        (openai.AuthenticationError("bad key", response=_response(401), body=None), llm_service.LLMConfigError),
        (openai.APIConnectionError(request=httpx.Request("POST", "http://x")), llm_service.LLMError),
    ],
)
def test_openai_errors_are_translated(monkeypatch, error, expected):
    monkeypatch.setattr(llm_service, "_get_client", lambda: fake_client(error=error))
    with pytest.raises(expected):
        llm_service.generate_answer([{"role": "user", "content": "hi"}])


def test_empty_answer_is_an_error(monkeypatch):
    monkeypatch.setattr(llm_service, "_get_client", lambda: fake_client(completion("")))
    with pytest.raises(llm_service.LLMError):
        llm_service.generate_answer([])
