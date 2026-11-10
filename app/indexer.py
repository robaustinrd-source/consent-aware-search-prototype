from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import List


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)


class LocalIndexer:
    """Read small, non-executable text formats strictly from a configured root."""
    supported_suffixes = {".txt", ".md", ".json", ".csv", ".html", ".htm", ".xml"}

    def __init__(self, allowed_root: Path, max_bytes: int = 10 * 1024 * 1024) -> None:
        self.allowed_root = allowed_root.expanduser().resolve()
        self.max_bytes = max_bytes
        self.allowed_root.mkdir(parents=True, exist_ok=True)

    def read_file(self, relative_path: str) -> str:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise ValueError("only paths relative to the configured ingest directory are allowed")
        path = (self.allowed_root / candidate).resolve(strict=True)
        if not path.is_relative_to(self.allowed_root):
            raise ValueError("path is outside the configured ingest directory")
        if not path.is_file():
            raise ValueError("path must refer to a regular file")
        if path.suffix.lower() not in self.supported_suffixes:
            raise ValueError("unsupported file type")
        if path.stat().st_size > self.max_bytes:
            raise ValueError("file exceeds configured size limit")
        raw = path.read_text(encoding="utf-8", errors="replace")
        suffix = path.suffix.lower()
        if suffix in {".html", ".htm", ".xml"}:
            parser = _HTMLTextExtractor()
            parser.feed(raw)
            raw = " ".join(parser.parts)
        elif suffix == ".json":
            try:
                raw = json.dumps(json.loads(raw), ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        return self.normalize_text(raw)

    @staticmethod
    def normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.replace("\r", " ")).strip()
