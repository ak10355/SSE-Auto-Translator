"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from core.utilities.exceptions import LocalizedException


class LlmError(LocalizedException):
    """Base class for OpenAI-compatible LLM translator errors."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "LLM translation failed!")


class LlmConfigurationError(LlmError):
    """Exception raised when required LLM settings are missing or invalid."""


class LlmApiKeyMissingError(LlmConfigurationError):
    """Exception raised when no API key is configured."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "An API key is required for LLM!")


class LlmBaseUrlInvalidError(LlmConfigurationError):
    """Exception raised when the LLM API base URL is invalid."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "A valid LLM API URL is required!")


class LlmModelMissingError(LlmConfigurationError):
    """Exception raised when no LLM model is selected."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Select an LLM model!")


class LlmPromptMissingError(LlmConfigurationError):
    """Exception raised when no system prompt is configured."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "A system prompt is required for LLM!")


class LlmNetworkError(LlmError):
    """Exception raised when the LLM API cannot be reached."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Could not reach the LLM API.")


class LlmRequestError(LlmError):
    """Exception raised when the LLM API rejects a request."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "LLM API request failed: {0}")


class LlmUnexpectedResponseError(LlmError):
    """Exception raised when an LLM response cannot be parsed."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "LLM API returned an unexpected response."
        )


class LlmEmptyTranslationError(LlmError):
    """Exception raised when an LLM returns an empty translation."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "LLM API returned an empty translation.")
