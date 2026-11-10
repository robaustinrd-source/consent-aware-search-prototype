from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional


class DocumentNormalizer:
    """Utility for whitespace normalization and text cleanup."""

    def normalize(self, text: str) -> str:
        return " ".join(text.split())


class OCRPipeline:
    """Small scaffold to support OCR/image/PDF processing behind a trusted worker."""

    def __init__(self, supported_extensions: Optional[Iterable[str]] = None) -> None:
        self.supported_extensions = set(supported_extensions or {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"})
        self.logger = logging.getLogger("ocr_pipeline")

    def supported(self, path: str | Path) -> bool:
        return Path(path).suffix.lower() in self.supported_extensions

    def extract(self, path: str | Path) -> str:
        target = Path(path)
        if not self.supported(target):
            raise ValueError(f"Unsupported OCR extension: {target.suffix}")
        self.logger.warning("OCR pipeline is a scaffold. Install OCR tooling before production use.")
        return target.read_text(encoding="utf-8", errors="replace") if target.suffix.lower() == ".txt" else ""


# Real OCR must run in an isolated worker or sandbox and must use explicit file allowlists.
