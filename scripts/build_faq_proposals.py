#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.services.faq.faq_matcher import FAQMatcher
from core.services.intent.intent_router import IntentRouter
from core.utils.language_detection import detect_language
from core.utils.query_translation import normalize_query_for_retrieval


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            items.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return items


def _load_seed_questions(seed_path: Path) -> set[str]:
    if not seed_path.exists():
        return set()
    try:
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    out: set[str] = set()
    for item in payload if isinstance(payload, list) else []:
        for pattern in item.get("question_patterns", []):
            lang = item.get("language") or detect_language(pattern)
            out.add(normalize_query_for_retrieval(pattern, lang).lower())
    return out


def _score_event(item: dict[str, Any], slow_threshold: float, low_conf_threshold: float) -> float:
    confidence = float(item.get("confidence", 1.0))
    elapsed = float(item.get("elapsed_seconds", 0.0))
    web_fallback = bool(item.get("web_fallback_used", False))
    citations_count = int(item.get("citations_count", 0))

    score = 1.0
    if elapsed >= slow_threshold:
        score += 1.4
    if confidence < low_conf_threshold:
        score += 1.8
    if web_fallback:
        score += 0.9
    if citations_count == 0:
        score += 0.5
    return score


def build_proposals(
    review_log_path: Path,
    faq_seed_path: Path,
    output_json_path: Path,
    output_md_path: Path,
    top_k: int,
    slow_threshold: float,
    low_conf_threshold: float,
) -> list[dict[str, Any]]:
    events = _load_jsonl(review_log_path)
    if not events:
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text("[]\n", encoding="utf-8")
        output_md_path.write_text("# FAQ Proposals\n\nNo events found.\n", encoding="utf-8")
        return []

    faq_matcher = FAQMatcher(str(faq_seed_path))
    intent_router = IntentRouter()
    normalized_seed = _load_seed_questions(faq_seed_path)
    grouped: dict[str, dict[str, Any]] = {}
    frequencies: Counter[str] = Counter()
    weighted_scores: defaultdict[str, float] = defaultdict(float)

    for item in events:
        question = (item.get("question") or "").strip()
        if not question:
            continue
        language = detect_language(question)
        normalized = normalize_query_for_retrieval(question, language).lower()
        if len(normalized) < 8:
            continue

        if normalized in normalized_seed:
            continue
        # Skip if existing FAQ already matches strongly.
        if faq_matcher.match(question, min_score=0.9):
            continue

        frequencies[normalized] += 1
        weighted_scores[normalized] += _score_event(item, slow_threshold, low_conf_threshold)

        if normalized not in grouped:
            grouped[normalized] = {
                "question": question,
                "normalized_question": normalized,
                "language": language,
                "intent": intent_router.classify(question),
                "suggested_section": "Review queue",
            }

    ranked = sorted(
        grouped.values(),
        key=lambda x: weighted_scores[x["normalized_question"]] * math.log2(2 + frequencies[x["normalized_question"]]),
        reverse=True,
    )
    proposals: list[dict[str, Any]] = []
    for item in ranked[:top_k]:
        norm = item["normalized_question"]
        proposals.append(
            {
                "question": item["question"],
                "normalized_question": norm,
                "language": item["language"],
                "intent": item["intent"],
                "frequency": frequencies[norm],
                "priority_score": round(weighted_scores[norm], 3),
                "suggested_section": item["suggested_section"],
                "suggested_answer": "",
                "suggested_patterns": [norm],
            }
        )

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(proposals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = ["# FAQ Proposals", ""]
    if not proposals:
        md_lines.append("No new candidates after deduplication.")
    else:
        for i, p in enumerate(proposals, start=1):
            md_lines.append(f"## {i}. {p['question']}")
            md_lines.append(f"- `intent`: {p['intent']}")
            md_lines.append(f"- `frequency`: {p['frequency']}")
            md_lines.append(f"- `priority_score`: {p['priority_score']}")
            md_lines.append(f"- `normalized`: {p['normalized_question']}")
            md_lines.append("")
    output_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return proposals


def append_review_queue(
    proposals: list[dict[str, Any]],
    queue_path: Path,
) -> int:
    existing: list[dict[str, Any]] = []
    if queue_path.exists():
        try:
            existing = json.loads(queue_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
    normalized_existing = {item.get("normalized_question", "") for item in existing}
    added = 0
    for proposal in proposals:
        if proposal["normalized_question"] in normalized_existing:
            continue
        existing.append(proposal)
        normalized_existing.add(proposal["normalized_question"])
        added += 1
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Build daily FAQ proposals from answer review events.")
    parser.add_argument("--review-log", default="logs/answer_review.jsonl")
    parser.add_argument("--faq-seed", default="data/sources/faq_seed.json")
    parser.add_argument("--output-json", default="data/processed/faq_proposals_daily.json")
    parser.add_argument("--output-md", default="data/processed/faq_proposals_daily.md")
    parser.add_argument("--review-queue", default="data/sources/faq_seed_review_queue.json")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--slow-threshold", type=float, default=12.0)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.55)
    parser.add_argument("--append-review-queue", action="store_true")
    args = parser.parse_args()

    proposals = build_proposals(
        review_log_path=Path(args.review_log),
        faq_seed_path=Path(args.faq_seed),
        output_json_path=Path(args.output_json),
        output_md_path=Path(args.output_md),
        top_k=args.top_k,
        slow_threshold=args.slow_threshold,
        low_conf_threshold=args.low_confidence_threshold,
    )
    print(f"Generated {len(proposals)} proposal(s)")

    if args.append_review_queue:
        added = append_review_queue(proposals, Path(args.review_queue))
        print(f"Added {added} proposal(s) to review queue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
