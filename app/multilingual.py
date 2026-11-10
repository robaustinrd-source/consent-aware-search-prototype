from __future__ import annotations

import re
from typing import Iterable, Optional


class LanguageProfile:
    def __init__(self, locale: str = "en", languages: Optional[Iterable[str]] = None,
                 preferred_formats: Optional[Iterable[str]] = None) -> None:
        self.locale = locale
        self.languages = list(languages or [locale])
        self.preferred_formats = list(preferred_formats or ["json", "text"])


def detect_language(text: str) -> str:
    """A lightweight heuristic for local prototypes only."""
    lower = text.casefold()
    if any(token in lower for token in ["hola", "gracias", "buenos", "adios", "por favor"]):
        return "es"
    if any(token in lower for token in ["bonjour", "merci", "français", "salut", "s'il"]):
        return "fr"
    if any(token in lower for token in ["hallo", "danke", "guten", "servus"]):
        return "de"
    return "en"


def normalize_text_for_language(text: str, language: str) -> str:
    result = re.sub(r"\s+", " ", text).strip()
    if language == "en":
        return result
    return result


# Production indexing should use a proper multilingual processing library and user-approved language settings.
