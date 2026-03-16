from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

from core.utils.language_detection import detect_language
from core.utils.query_translation import normalize_query_for_retrieval


def generate_faq_entries(processed_dir: str) -> int:
    faq_path = Path("data/processed/faq_generated.md")
    entries = []

    for text_file in Path(processed_dir).glob("*.txt"):
        question = f"What does {text_file.stem} describe?"
        answer = "Auto-generated placeholder answer from processed compliance chunk."
        entries.append(f"## {question}\n\n{answer}\n")

    faq_path.write_text("\n".join(entries), encoding="utf-8")
    return len(entries)


def build_usage_faq_candidates(
    database_path: str = "gxp_platform.db",
    output_path: str = "data/processed/faq_candidates_from_usage.json",
    limit: int = 50,
) -> int:
    db_file = Path(database_path)
    if not db_file.exists():
        Path(output_path).write_text("[]", encoding="utf-8")
        return 0

    conn = sqlite3.connect(db_file)
    try:
        rows = conn.execute("SELECT query FROM usage_logs WHERE query IS NOT NULL AND TRIM(query) <> ''").fetchall()
    finally:
        conn.close()

    counter: Counter[str] = Counter()
    for (query,) in rows:
        language = detect_language(query)
        normalized = normalize_query_for_retrieval(query, language).lower()
        if len(normalized) < 8:
            continue
        counter[normalized] += 1

    payload = []
    for normalized_query, frequency in counter.most_common(limit):
        payload.append(
            {
                "question": normalized_query,
                "language": detect_language(normalized_query),
                "frequency": frequency,
                "suggested_section": "Usage-derived candidate",
                "suggested_answer": "",
            }
        )

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload)


if __name__ == "__main__":
    generated = generate_faq_entries("data/processed")
    candidates = build_usage_faq_candidates()
    print(f"Generated {generated} FAQ markdown entries")
    print(f"Generated {candidates} FAQ candidates from usage logs")
