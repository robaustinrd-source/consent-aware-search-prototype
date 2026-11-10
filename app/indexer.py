from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)


class LocalIndexer:
    def __init__(self) -> None:
        self.supported_suffixes = {".txt", ".md", ".json", ".csv", ".html", ".htm"}

    def read_file(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)

        text = path.read_text(encoding="utf-8", errors="ignore")
        suffix = path.suffix.lower()

        if suffix in {".html", ".htm"}:
            return self._extract_html_text(text)
        if suffix == ".json":
            try:
                payload = json.loads(text)
                return json.dumps(payload, ensure_ascii=False)
            except json.JSONDecodeError:
                return text
        if suffix == ".csv":
            return text
        return text

    def _extract_html_text(self, html: str) -> str:
        parser = _HTMLTextExtractor()
        parser.feed(html)
        return " ".join(parser.parts)

    @staticmethod
    def normalize_text(text: str) -> str:
        text = text.replace("\r", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()
