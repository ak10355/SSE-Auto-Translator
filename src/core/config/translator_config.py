"""
Copyright (c) Cutleast
"""

from typing import Annotated, ClassVar, Optional, override

from cutleast_core_lib.core.config.base_config import BaseConfig

from core.translator.apis import TranslatorApi


class TranslatorConfig(BaseConfig):
    """
    Class for translator settings.
    """

    DEFAULT_PROMPT: ClassVar[str] = (
        "You are a professional localization translator for The Elder Scrolls V: "
        "Skyrim and Skyrim mods. Use established Skyrim and The Elder Scrolls "
        "terminology, lore, names, and the appropriate in-game style. Preserve line "
        "breaks, formatting, placeholders, markup, and control sequences exactly. "
        "When translating into Russian, use informal singular forms of 'you' (ты, "
        "тебя, тебе, тобой, твой, and related forms) by default. Use formal 'вы' "
        "forms only when the context clearly requires respectful address, such as "
        "speaking to an adult stranger, a jarl, thane, king, queen, or another "
        "high-ranking character. Use plural 'вы' forms when 'you' clearly addresses "
        "multiple people, as in 'you guys'. An official vanilla Skyrim glossary may "
        "be added to the request. When it is present, use its translations as "
        "authoritative terminology and inflect them naturally for the sentence, "
        "including grammatical case and singular/plural number."
    )
    """Default system prompt used for LLM translations."""

    translator: TranslatorApi = TranslatorApi.Google
    """The translator API to use for machine translations."""

    api_key: Annotated[
        Optional[str],
        BaseConfig.PropertyMarker.ExcludeFromLogging,
    ] = None
    """Shared API key for the selected translator."""

    prompt: str = DEFAULT_PROMPT
    """Editable system prompt for the LLM translator."""

    llm_base_url: str = "http://127.0.0.1:8888/v1"
    """OpenAI-compatible API base URL, including the API version path."""

    llm_model: Optional[str] = None
    """The model ID selected from the configured LLM API."""

    reasoning_effort: Optional[str] = "none"
    """OpenAI-compatible reasoning effort; ``none`` disables reasoning."""

    show_confirmation_dialogs: bool = True
    """Whether to ask for confirmation before starting a machine translation."""

    @override
    @staticmethod
    def get_config_name() -> str:
        return "translator/config.json"
