from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from uuid import uuid4


class LocalSearchEngine:
    def __init__(self) -> None:
        self.documents: Dict[str, Dict[str, object]] = {}
        self.collection_map: Dict[str, Set[str]] = defaultdict(set)

    def index_document(
        self,
        *,
        title: str,
        text: str,
        collection_id: str,
        source_id: str,
        consent_required: bool = False,
    ) -> Dict[str, object]:
        doc_id = f"doc-{uuid4().hex[:10]}"
        normalized = self._normalize(text)
        doc = {
            "document_id": doc_id,
            "title": title,
            "text": normalized,
            "collection_id": collection_id,
            "source_id": source_id,
            "consent_required": consent_required,
            "token_count": len(normalized.split()),
        }
        self.documents[doc_id] = doc
        self.collection_map[collection_id].add(doc_id)
        return doc

    def search(
        self,
        *,
        query: str,
        collections: Optional[List[str]] = None,
        include_private: bool = False,
        language: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        if not query:
            return []

        query_terms = self._tokenize(query)
        collection_ids = set(collections or self.collection_map.keys())

        results: List[Dict[str, object]] = []
        for doc_id, doc in self.documents.items():
            if doc["collection_id"] not in collection_ids:
                continue
            if bool(doc["consent_required"]) and not include_private:
                continue

            score = self._score_document(doc["text"], query_terms)
            if score <= 0:
                continue

            snippet = self._make_snippet(doc["text"], query_terms)
            results.append(
                {
                    "document_id": doc["document_id"],
                    "title": doc["title"],
                    "collection_id": doc["collection_id"],
                    "source_id": doc["source_id"],
                    "score": round(score, 4),
                    "snippet": snippet,
                    "consent_required": bool(doc["consent_required"]),
                }
            )

        return sorted(results, key=lambda item: item["score"], reverse=True)

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.lower().replace("\n", " ")
        return " ".join(normalized.split())

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token for token in text.lower().split() if token]

    @staticmethod
    def _score_document(document_text: str, query_terms: List[str]) -> float:
        tokens = LocalSearchEngine._tokenize(document_text)
        if not tokens:
            return 0.0
        document_freq = defaultdict(int)
        for token in tokens:
            document_freq[token] += 1
        score = 0.0
        for term in query_terms:
            if term in document_freq:
                score += document_freq[term]
        if query_terms:
            score += 0.1 * len(set(query_terms) & set(tokens))
        return score

    @staticmethod
    def _make_snippet(text: str, query_terms: List[str]) -> str:
        lower = text.lower()
        hits: List[str] = []
        for term in query_terms:
            idx = lower.find(term)
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(text), idx + 80)
                hits.append(text[start:end].strip())
        if hits:
            return "... " + " ... ".join(hits) + " ..."
        return text[:160]
