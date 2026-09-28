"""
Copyright (c) Cutleast
"""

import pytest
import requests
import requests_mock as requests_mock_module

from core.config.translator_config import TranslatorConfig
from core.file_types.plugin.string import PluginString
from core.translator.exceptions import (
    LlmApiKeyMissingError,
    LlmModelMissingError,
    LlmNetworkError,
    LlmRequestError,
    LlmUnexpectedResponseError,
)
from core.translator.llm import LlmTranslator
from core.translator.vanilla_glossary import VanillaGlossary
from core.utilities.game_language import GameLanguage


class TestLlmTranslator:
    """Tests `core.translator.llm.LlmTranslator`."""

    BASE_URL = "http://127.0.0.1:8888/v1"
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
    MODEL = "local-model"

    @classmethod
    def get_config(cls) -> TranslatorConfig:
        """Creates an isolated valid OpenAI-compatible LLM configuration."""

        return TranslatorConfig.model_validate(
            {
                "llm_base_url": cls.BASE_URL,
                "api_key": "local-test-key",
                "llm_model": cls.MODEL,
            }
        )

    def test_requires_api_key(self) -> None:
        """Tests that an LLM API key is mandatory."""

        config = self.get_config()
        config.api_key = None

        with pytest.raises(LlmApiKeyMissingError):
            LlmTranslator(config)

    def test_requires_model(self) -> None:
        """Tests that a loaded model must be selected."""

        config = self.get_config()
        config.llm_model = None

        with pytest.raises(LlmModelMissingError):
            LlmTranslator(config)

    def test_gets_loaded_models(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests the OpenAI-compatible models endpoint and authentication."""

        requests_mock.get(
            f"{self.BASE_URL}/models",
            json={
                "data": [
                    {"id": "model-b"},
                    {"id": "model-a"},
                    {"id": "model-a"},
                ]
            },
        )

        models = LlmTranslator.get_available_models(
            self.BASE_URL, "local-test-key"
        )

        assert models == ["model-a", "model-b"]
        assert requests_mock.last_request is not None
        assert (
            requests_mock.last_request.headers["Authorization"]
            == "Bearer local-test-key"
        )

    def test_translates_text(self, requests_mock: requests_mock_module.Mocker) -> None:
        """Tests the OpenAI-compatible translation request format."""

        requests_mock.post(
            f"{self.BASE_URL}/chat/completions",
            json={"choices": [{"message": {"content": "Привет, странник!"}}]},
        )
        translator = LlmTranslator(self.get_config())

        result = translator.translate_uncached(
            "Hello, wanderer!", GameLanguage.Russian
        )

        assert result == "Привет, странник!"
        assert requests_mock.last_request is not None
        request_json = requests_mock.last_request.json()
        assert request_json["model"] == self.MODEL
        assert request_json["stream"] is False
        assert request_json["reasoning_effort"] == "none"
        assert request_json["messages"][1]["content"] == "Hello, wanderer!"
        assert "Skyrim" in request_json["messages"][0]["content"]
        assert "Russian" in request_json["messages"][0]["content"]

    def test_adds_matching_vanilla_terms_to_system_prompt(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests that NPC and location names are included as official terminology."""

        requests_mock.post(
            f"{self.BASE_URL}/chat/completions",
            json={"choices": [{"message": {"content": "Перевод"}}]},
        )
        glossary = VanillaGlossary(
            [
                PluginString(
                    original="Ulfric Stormcloak",
                    string="Ульфрик Буревестник",
                    form_id="0001414D|Skyrim.esm",
                    type="NPC_ FULL",
                ),
                PluginString(
                    original="Windhelm",
                    string="Виндхельм",
                    form_id="00018A57|Skyrim.esm",
                    type="LCTN FULL",
                ),
                PluginString(
                    original="Stone of Barenziah",
                    string="Камень Барензии",
                    form_id="0006D626|Skyrim.esm",
                    type="MESG FULL",
                ),
            ]
        )

        LlmTranslator(self.get_config(), glossary).translate_uncached(
            "We captured Windhelm, killed Ulfric Stormcloak, and found Stones of "
            "Barenziah.",
            GameLanguage.Russian,
        )

        assert requests_mock.last_request is not None
        prompt = requests_mock.last_request.json()["messages"][0]["content"]
        assert "Windhelm -> Виндхельм" in prompt
        assert "Ulfric Stormcloak -> Ульфрик Буревестник" in prompt
        assert "Stones of Barenziah -> Камень Барензии" in prompt
        assert "inflect them naturally" in prompt

    def test_translates_through_gemini_openai_endpoint(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests Gemini through the same OpenAI-compatible request format."""

        requests_mock.post(
            f"{self.GEMINI_BASE_URL}/chat/completions",
            json={"choices": [{"message": {"content": "Привет"}}]},
        )
        config = TranslatorConfig.model_validate(
            {
                "llm_base_url": self.GEMINI_BASE_URL,
                "api_key": "gemini-test-key",
                "llm_model": "gemini-2.5-flash",
            }
        )

        result = LlmTranslator(config).translate_uncached(
            "Hello", GameLanguage.Russian
        )

        assert result == "Привет"
        assert requests_mock.last_request is not None
        assert (
            requests_mock.last_request.headers["Authorization"]
            == "Bearer gemini-test-key"
        )

    def test_reports_api_error(self, requests_mock: requests_mock_module.Mocker) -> None:
        """Tests that a server error message is retained."""

        requests_mock.post(
            f"{self.BASE_URL}/chat/completions",
            status_code=404,
            json={"error": {"message": "Model is not loaded"}},
        )

        with pytest.raises(LlmRequestError, match="Model is not loaded"):
            LlmTranslator(self.get_config()).translate_uncached(
                "Hello", GameLanguage.Russian
            )

    def test_reports_malformed_response(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests that malformed OpenAI responses are rejected."""

        requests_mock.post(f"{self.BASE_URL}/chat/completions", json={"choices": []})

        with pytest.raises(LlmUnexpectedResponseError):
            LlmTranslator(self.get_config()).translate_uncached(
                "Hello", GameLanguage.Russian
            )

    def test_reports_network_error(self, requests_mock: requests_mock_module.Mocker) -> None:
        """Tests that connection failures are not hidden."""

        requests_mock.post(
            f"{self.BASE_URL}/chat/completions",
            exc=requests.ConnectionError("No connection"),
        )

        with pytest.raises(LlmNetworkError):
            LlmTranslator(self.get_config()).translate_uncached(
                "Hello", GameLanguage.Russian
            )

    def test_cache_id_changes_with_model_and_prompt(self) -> None:
        """Tests that model and prompt changes cannot reuse old translations."""

        first_config = self.get_config()
        second_config = self.get_config()
        second_config.llm_model = "other-model"
        second_config.prompt = "Different prompt"

        first_id = LlmTranslator(first_config).get_cache_id(
            "Text", GameLanguage.Russian
        )
        second_id = LlmTranslator(second_config).get_cache_id(
            "Text", GameLanguage.Russian
        )

        assert first_id != second_id

    def test_cache_id_changes_with_reasoning_effort(self) -> None:
        """Tests that reasoning settings cannot reuse old translations."""

        first_config = self.get_config()
        second_config = self.get_config()
        second_config.reasoning_effort = "low"

        first_id = LlmTranslator(first_config).get_cache_id(
            "Text", GameLanguage.Russian
        )
        second_id = LlmTranslator(second_config).get_cache_id(
            "Text", GameLanguage.Russian
        )

        assert first_id != second_id
