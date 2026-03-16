from __future__ import annotations

import json
from pathlib import Path

from core.utils.language_detection import detect_language
from core.utils.query_translation import normalize_query_for_retrieval


class FAQMatcher:
    def __init__(self, faq_path: str = "data/sources/faq_seed.json") -> None:
        self.faq_path = Path(faq_path)
        self.entries = self._load_entries()

    def _load_entries(self) -> list[dict]:
        if not self.faq_path.exists():
            return []
        try:
            payload = json.loads(self.faq_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def _score_match(query: str, pattern: str) -> float:
        q_terms = set(query.split())
        p_terms = set(pattern.split())
        if not q_terms or not p_terms:
            return 0.0
        overlap = len(q_terms & p_terms) / max(1, len(p_terms))
        phrase_bonus = 0.35 if pattern in query else 0.0
        return overlap + phrase_bonus

    def match(self, question: str, min_score: float = 0.85) -> dict | None:
        language = detect_language(question)
        normalized = normalize_query_for_retrieval(question, language).lower()
        best: tuple[float, dict] | None = None

        for entry in self.entries:
            entry_language = entry.get("language")
            if entry_language and entry_language != language:
                continue
            for pattern in entry.get("question_patterns", []):
                normalized_pattern = normalize_query_for_retrieval(pattern, language).lower()
                score = self._score_match(normalized, normalized_pattern)
                if best is None or score > best[0]:
                    best = (
                        score,
                        {
                            "answer": entry.get("answer", ""),
                            "citation": {
                                "source": "internal_faq",
                                "section": entry.get("section") or entry.get("id") or "FAQ",
                                "page_start": None,
                                "page_end": None,
                                "snippet": entry.get("answer", "")[:220],
                            },
                            "score": score,
                        },
                    )
        if best and best[0] >= min_score:
            return best[1]
        return None
