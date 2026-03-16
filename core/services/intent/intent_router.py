from __future__ import annotations

import re

from core.utils.language_detection import detect_language
from core.utils.query_translation import normalize_query_for_retrieval


class IntentRouter:
    def classify(self, question: str) -> str:
        language = detect_language(question)
        normalized = normalize_query_for_retrieval(question, language).lower()
        raw = (question or "").lower()
        text = f"{raw} {normalized}"

        if self._extract_cleanroom_grade(text):
            return "cleanroom_grade_limit"
        if any(k in text for k in ("supplier", "nha cung cap", "phe duyet nha cung cap")):
            return "supplier_sop"
        if any(k in text for k in ("nhiet do kho", "temperature", "excursion", "mapping")):
            return "temperature_control"
        if any(k in text for k in ("alcoa", "data integrity", "du lieu", "truy vet du lieu")):
            return "data_integrity"
        if any(k in text for k in ("deviation", "sai lech", "capa", "root cause")):
            return "deviation_capa"
        if any(k in text for k in ("change control", "kiem soat thay doi", "thay doi")):
            return "change_control"
        if any(k in text for k in ("validation protocol", "tham dinh", "de cuong tham dinh")):
            return "validation"
        if any(k in text for k in ("hold time", "ton tru ban dau", "initial hold time")):
            return "hold_time"
        if any(k in text for k in ("vi sinh", "clean room", "cleanroom", "grade", "particle", "cfu")):
            return "cleanroom_general"
        return "general"

    @staticmethod
    def _extract_cleanroom_grade(text: str) -> str | None:
        patterns = {
            "A": [r"cap\s*sach\s*a", r"grade\s*a"],
            "B": [r"cap\s*sach\s*b", r"grade\s*b"],
            "C": [r"cap\s*sach\s*c", r"grade\s*c"],
            "D": [r"cap\s*sach\s*d", r"grade\s*d"],
        }
        low = (text or "").lower()
        for grade, items in patterns.items():
            if any(re.search(p, low) for p in items):
                return grade
        return None
