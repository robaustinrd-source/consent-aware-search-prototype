from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set

from .storage import SQLiteStore


class LocalSearchEngine:
    """Persistent, local lexical search. Private documents are hidden unless scoped access is granted."""

    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def index_document(self, *, title: str, text: str, collection_id: str,
                       source_id: str, is_private: bool = False) -> Dict[str, Any]:
        return self.store.save_document(title=title, text=text, collection_id=collection_id,
                                        source_id=source_id, is_private=is_private)

    def list_collections(self) -> List[str]:
        return self.store.list_collections()

    def get_document(self, document_id: str, *, allowed_private_collection: str | None = None) -> Dict[str, Any] | None:
        doc = self.store.get_document(document_id)
        if doc and doc["is_private"] and doc["collection_id"] != allowed_private_collection:
            return None
        if doc:
            doc.pop("content_hash", None)
        return doc

    def search(self, *, query: str, collections: Optional[List[str]] = None,
               authorized_collection: str | None = None, limit: int = 20) -> List[Dict[str, Any]]:
        terms = self._tokenize(query)
        if not terms:
            return []
        docs = self.store.documents(collections)
        visible = [d for d in docs if not d["is_private"] or d["collection_id"] == authorized_collection]
        if not visible:
            return []
        doc_tokens = [self._tokenize(d["text"]) for d in visible]
        avgdl = sum(len(tokens) for tokens in doc_tokens) / max(1, len(doc_tokens))
        n = len(visible)
        df = Counter(term for term in set(terms) for tokens in doc_tokens if term in set(tokens))
        results = []
        for doc, tokens in zip(visible, doc_tokens):
            frequencies = Counter(tokens)
            score = 0.0
            for term in terms:
                frequency = frequencies[term]
                if frequency:
                    idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                    denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * len(tokens) / max(avgdl, 1))
                    score += idf * frequency * 2.2 / denominator
            if score <= 0:
                continue
            snippet = self._snippet(doc["text"], terms)
            results.append({"document_id": doc["document_id"], "title": doc["title"],
                            "collection_id": doc["collection_id"], "source_id": doc["source_id"],
                            "score": round(score, 5), "snippet": snippet,
                            "is_private": bool(doc["is_private"])})
        return sorted(results, key=lambda item: item["score"], reverse=True)[:max(1, min(limit, 100))]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)

    @staticmethod
    def _snippet(text: str, terms: List[str]) -> str:
        folded = text.casefold()
        position = min((folded.find(term.casefold()) for term in terms if folded.find(term.casefold()) >= 0), default=0)
        start, end = max(0, position - 70), min(len(text), position + 180)
        return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")
