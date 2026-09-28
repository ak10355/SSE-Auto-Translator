"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.core.utilities.singleton import Singleton

from core.config.translator_config import TranslatorConfig
from core.database.database import TranslationDatabase
from core.string.types import String

from .apis import TranslatorApi
from .deepl import DeepLTranslator
from .google import GoogleTranslator
from .llm import LlmTranslator
from .translator import Translator
from .vanilla_glossary import VanillaGlossary


class TranslatorService(Singleton):
    """
    Singleton class for providing a translator instance for the current translator
    configuration.
    """

    __translator_config: TranslatorConfig
    __database: TranslationDatabase | None
    __vanilla_glossary: VanillaGlossary | None = None

    def __init__(
        self,
        translator_config: TranslatorConfig,
        database: TranslationDatabase | None = None,
    ) -> None:
        """
        Args:
            translator_config (TranslatorConfig): The app-wide translator configuration.
            database: Loaded translation database for vanilla terminology.
        """

        super().__init__()

        self.__translator_config = translator_config
        self.__database = database

    def get_translator(self) -> Translator:
        """
        Returns:
            Translator: A translator instance for the current translator configuration.
        """

        translators: dict[TranslatorApi, type[Translator]] = {
            TranslatorApi.Google: GoogleTranslator,
            TranslatorApi.DeepL: DeepLTranslator,
        }

        if self.__translator_config.translator == TranslatorApi.LLM:
            return LlmTranslator(
                self.__translator_config, self.__get_vanilla_glossary()
            )

        translator_cls: type[Translator] = translators[
            self.__translator_config.translator
        ]

        return translator_cls(self.__translator_config)

    def __get_vanilla_glossary(self) -> VanillaGlossary | None:
        """Lazily creates the glossary only when an LLM is selected."""

        if self.__database is None:
            return None
        if self.__vanilla_glossary is None:
            strings: list[String] = [
                string
                for modfile_strings in self.__database.vanilla_translation.strings.values()
                for string in modfile_strings
            ]
            self.__vanilla_glossary = VanillaGlossary(strings)
        return self.__vanilla_glossary
