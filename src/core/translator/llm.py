"""
Copyright (c) Cutleast
"""

import json
from typing import Any, final, override
from urllib.parse import urlparse

import requests
from cutleast_core_lib.core.utilities.hash import sha256_hash

from core.config.translator_config import TranslatorConfig
from core.utilities.game_language import GameLanguage

from .exceptions import (
    LlmApiKeyMissingError,
    LlmBaseUrlInvalidError,
    LlmEmptyTranslationError,
    LlmModelMissingError,
    LlmNetworkError,
    LlmPromptMissingError,
    LlmRequestError,
    LlmUnexpectedResponseError,
)
from .translator import Translator
from .vanilla_glossary import VanillaGlossary


@final
class LlmTranslator(Translator):
    """Translator using an OpenAI-compatible LLM API."""

    REQUEST_TIMEOUT: int = 120

    __base_url: str
    __api_key: str
    __model: str
    __prompt: str
    __reasoning_effort: str | None
    __vanilla_glossary: VanillaGlossary | None

    @override
    def __init__(
        self, config: TranslatorConfig, vanilla_glossary: VanillaGlossary | None = None
    ) -> None:
        """Initializes the configured LLM API with its model and prompt."""

        super().__init__(config)

        self.__base_url = self.normalize_base_url(config.llm_base_url)
        if config.api_key is None or not config.api_key.strip():
            raise LlmApiKeyMissingError()
        if config.llm_model is None or not config.llm_model.strip():
            raise LlmModelMissingError()
        if not config.prompt.strip():
            raise LlmPromptMissingError()

        self.__api_key = config.api_key.strip()
        self.__model = config.llm_model.strip()
        self.__prompt = config.prompt.strip()
        self.__reasoning_effort = config.reasoning_effort
        self.__vanilla_glossary = vanilla_glossary

    @staticmethod
    def normalize_base_url(base_url: str) -> str:
        """Validates and normalizes a configured OpenAI-compatible API URL."""

        normalized: str = base_url.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise LlmBaseUrlInvalidError()
        return normalized

    @classmethod
    def get_available_models(cls, base_url: str, api_key: str) -> list[str]:
        """Returns IDs for models exposed by the configured LLM API."""

        normalized_url = cls.normalize_base_url(base_url)
        if not api_key.strip():
            raise LlmApiKeyMissingError()

        try:
            response = requests.get(
                f"{normalized_url}/models",
                headers={"Authorization": f"Bearer {api_key.strip()}"},
                timeout=cls.REQUEST_TIMEOUT,
                allow_redirects=False,
            )
        except requests.RequestException as ex:
            raise LlmNetworkError() from ex

        cls.raise_for_response_error(response)
        try:
            data = response.json()["data"]
            if not isinstance(data, list):
                raise TypeError("LLM models response data must be a list")
            models = [
                model["id"]
                for model in data
                if isinstance(model, dict)
                and isinstance(model.get("id"), str)
                and model["id"].strip()
            ]
        except (KeyError, TypeError, ValueError) as ex:
            raise LlmUnexpectedResponseError() from ex

        return sorted(set(models))

    @override
    def translate_uncached(self, text: str, dst: GameLanguage) -> str:
        """Translates one text through the selected LLM model."""

        if not text:
            return text

        payload: dict[str, Any] = {
            "model": self.__model,
            "stream": False,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": self.__get_system_prompt(text, dst),
                },
                {"role": "user", "content": text},
            ],
        }
        if self.__reasoning_effort is not None:
            payload["reasoning_effort"] = self.__reasoning_effort

        try:
            response = requests.post(
                f"{self.__base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.__api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.REQUEST_TIMEOUT,
                allow_redirects=False,
            )
        except requests.RequestException as ex:
            raise LlmNetworkError() from ex

        self.raise_for_response_error(response)
        try:
            translated = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as ex:
            raise LlmUnexpectedResponseError() from ex

        if not isinstance(translated, str):
            raise LlmUnexpectedResponseError()
        if not translated.strip():
            raise LlmEmptyTranslationError()

        return translated

    @override
    def get_cache_id(self, text: str, dst: GameLanguage) -> str:
        """Generates a cache ID including all output-affecting LLM settings."""

        data = json.dumps(
            [
                self.__class__.__name__,
                self.__base_url,
                self.__model,
                self.__prompt,
                self.__reasoning_effort,
                self.__vanilla_glossary.id if self.__vanilla_glossary else None,
                text,
                dst.name,
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return sha256_hash(data.encode())

    def __get_system_prompt(self, text: str, dst: GameLanguage) -> str:
        """Builds the system prompt, including relevant official terminology."""

        prompt = (
            f"{self.__prompt}\n\nTranslate the user's English text into {dst.value}. "
            "Return only the translated text, without quotes, labels, explanations, "
            "or alternatives."
        )
        if self.__vanilla_glossary is None:
            return prompt

        terms = self.__vanilla_glossary.get_matches(text)
        if not terms:
            return prompt

        glossary = "\n".join(
            f"- {term.original} -> {term.translation}" for term in terms
        )
        return (
            f"{prompt}\n\nOfficial vanilla Skyrim glossary for exact phrases in the "
            "user text:\n"
            f"{glossary}\n\nUse these translations as authoritative terminology. Keep "
            "proper names recognizable and inflect them naturally when required by "
            "the target language, including grammatical case and singular/plural "
            "number."
        )

    @staticmethod
    def raise_for_response_error(response: requests.Response) -> None:
        """Raises a localized exception for redirects and failed API responses."""

        if 300 <= response.status_code < 400:
            raise LlmRequestError(f"HTTP {response.status_code}")
        try:
            response.raise_for_status()
        except requests.HTTPError as ex:
            raise LlmRequestError(LlmTranslator.get_error_message(response)) from ex

    @staticmethod
    def get_error_message(response: requests.Response) -> str:
        """Extracts a useful error message from an OpenAI-compatible error response."""

        try:
            error = response.json().get("error")
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                return error["message"].strip() or f"HTTP {response.status_code}"
            if isinstance(error, str) and error.strip():
                return error.strip()
        except (AttributeError, TypeError, ValueError):
            pass
        return f"HTTP {response.status_code}"
