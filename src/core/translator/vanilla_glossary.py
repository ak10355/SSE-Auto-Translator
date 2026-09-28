"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from cutleast_core_lib.core.utilities.hash import sha256_hash

from core.file_types.plugin.string import PluginString
from core.string.types import String


@dataclass(frozen=True)
class GlossaryTerm:
    """One official source-to-target terminology pair."""

    original: str
    """English term found in the source text."""

    translation: str
    """Official localized form of the term."""


class VanillaGlossary:
    """Matches names and locations from the bundled vanilla translation."""

    MAX_MATCHES = 20
    """Maximum number of terminology pairs included in one LLM request."""

    ADDITIONAL_TERM_TYPES = frozenset({"QUST NNAM"})
    """Named fields without a ``FULL`` subrecord, currently quest objectives."""

    __terms_by_initial: dict[str, tuple[GlossaryTerm, ...]]
    __id: str

    def __init__(self, strings: Iterable[String]) -> None:
        """Builds a lookup index from loaded vanilla translation strings."""

        terms_by_original: dict[str, GlossaryTerm] = {}
        for string in strings:
            if not isinstance(string, PluginString) or not self.__is_term(string):
                continue
            if string.string is None:
                continue

            original = string.original.strip()
            translation = string.string.strip()
            if not original or not translation or original.casefold() == translation.casefold():
                continue

            terms_by_original.setdefault(
                original.casefold(), GlossaryTerm(original, translation)
            )

        for term in list(terms_by_original.values()):
            plural = self.__get_plural_variant(term.original)
            if plural is not None:
                terms_by_original.setdefault(plural.casefold(), GlossaryTerm(plural, term.translation))

        terms_by_initial: dict[str, list[GlossaryTerm]] = {}
        for term in terms_by_original.values():
            terms_by_initial.setdefault(term.original[0].casefold(), []).append(term)

        self.__terms_by_initial = {
            initial: tuple(sorted(terms, key=lambda term: len(term.original), reverse=True))
            for initial, terms in terms_by_initial.items()
        }
        index_data = "\n".join(
            f"{term.original}\0{term.translation}"
            for term in sorted(
                terms_by_original.values(), key=lambda term: term.original.casefold()
            )
        )
        self.__id = sha256_hash(index_data.encode())

    @property
    def id(self) -> str:
        """Returns a stable ID for cache invalidation."""

        return self.__id

    def get_matches(self, text: str) -> list[GlossaryTerm]:
        """Returns the longest non-overlapping glossary terms in ``text``."""

        normalized_text = text.casefold()
        matches: list[GlossaryTerm] = []
        position = 0

        while position < len(text) and len(matches) < self.MAX_MATCHES:
            if position and self.__is_word_character(normalized_text[position - 1]):
                position += 1
                continue

            candidates = self.__terms_by_initial.get(normalized_text[position], ())
            for term in candidates:
                term_end = position + len(term.original)
                if (
                    normalized_text.startswith(term.original.casefold(), position)
                    and (
                        term_end == len(text)
                        or not self.__is_word_character(normalized_text[term_end])
                    )
                ):
                    matches.append(term)
                    position = term_end
                    break
            else:
                position += 1

        return matches

    @staticmethod
    def __is_word_character(char: str) -> bool:
        """Returns whether ``char`` prevents a phrase boundary."""

        return char.isalnum() or char == "_"

    @classmethod
    def __is_term(cls, string: PluginString) -> bool:
        """Returns whether a plugin field represents named game terminology."""

        return string.type.endswith(" FULL") or string.type in cls.ADDITIONAL_TERM_TYPES

    @staticmethod
    def __get_plural_variant(original: str) -> str | None:
        """Creates a simple plural variant for names such as ``Stone of Barenziah``."""

        first_word, separator, remainder = original.partition(" of ")
        if not separator or not first_word.isalpha() or len(first_word) < 3:
            return None
        if first_word.endswith(("s", "x", "z", "ch", "sh")):
            plural = f"{first_word}es"
        elif first_word.endswith("y") and len(first_word) > 1 and first_word[-2] not in "aeiou":
            plural = f"{first_word[:-1]}ies"
        else:
            plural = f"{first_word}s"
        return f"{plural}{separator}{remainder}"
