#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.api.database import SessionLocal
from apps.api.models import User
from apps.api.services.chat_service import ask_question_for_user
from configs.settings import settings
from core.services.intent.intent_router import IntentRouter


INTENT_PROMPTS = {
    "cleanroom_grade_limit": [
        "Tieu chuan vi sinh cap sach C theo Annex 1 la gi?",
        "Gioi han vi sinh cap sach B gom nhung chi tieu nao?",
    ],
    "temperature_control": [
        "Quy trinh kiem soat nhiet do kho thuoc GDP gom gi?",
        "Temperature excursion trong kho duoc xu ly nhu the nao?",
    ],
    "supplier_sop": [
        "SOP danh gia nha cung cap nguyen lieu can noi dung nao?",
        "Phe duyet nha cung cap GMP can bao cao gi?",
    ],
    "data_integrity": [
        "ALCOA+ trong GMP duoc ap dung the nao?",
        "Data integrity can kiem soat nhung diem nao?",
    ],
    "deviation_capa": [
        "Quy trinh deviation va CAPA gom cac buoc nao?",
        "Khi nao can mo CAPA sau sai lech?",
    ],
    "change_control": [
        "Change control trong GMP can danh gia tac dong gi?",
        "Thay doi quy trinh san xuat can phe duyet ra sao?",
    ],
    "validation": [
        "Validation protocol can co cac muc nao?",
        "De cuong tham dinh quy trinh gom gi?",
    ],
    "hold_time": [
        "Hold time duoc thiet lap theo nguyen tac nao?",
        "Thoi gian ton tru ban dau can duoc chung minh ra sao?",
    ],
}


def _parse_admin_user_id() -> int | None:
    for part in settings.admin_user_ids.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            return int(part)
        except ValueError:
            continue
    return None


def _load_review_queue(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    out: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            question = (item.get("question") or "").strip()
            if question:
                out.append(question)
    return out


def _build_training_questions(limit: int, queue_questions: list[str]) -> list[str]:
    intent_router = IntentRouter()
    selected: list[str] = []
    seen = set()

    for question in queue_questions:
        if question in seen:
            continue
        seen.add(question)
        selected.append(question)
        if len(selected) >= limit:
            return selected

    # Fill missing slots with curated prompts across intents.
    for prompts in INTENT_PROMPTS.values():
        for question in prompts:
            if question in seen:
                continue
            seen.add(question)
            selected.append(question)
            if len(selected) >= limit:
                return selected

    # Ensure coverage by adding one per intent if still short.
    for intent, prompts in INTENT_PROMPTS.items():
        for question in prompts:
            if question in seen:
                continue
            if intent_router.classify(question) == intent:
                selected.append(question)
                seen.add(question)
                if len(selected) >= limit:
                    return selected
    return selected


def run_training_once(
    admin_user_id: int,
    queue_path: Path,
    output_path: Path,
    limit: int,
) -> dict:
    queue_questions = _load_review_queue(queue_path)
    questions = _build_training_questions(limit=limit, queue_questions=queue_questions)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == admin_user_id).first()
        if not user:
            raise RuntimeError(f"Admin user id={admin_user_id} not found")

        rows: list[dict] = []
        for question in questions:
            result = ask_question_for_user(db=db, user=user, question=question)
            rows.append(
                {
                    "question": question,
                    "confidence": float(result.get("confidence", 0.0)),
                    "cached": bool(result.get("cached", False)),
                    "elapsed_seconds": float(result.get("elapsed_seconds", 0.0)),
                    "answer_mode": result.get("answer_mode", "unknown"),
                    "web_fallback_used": bool(result.get("web_fallback_used", False)),
                    "citations_count": len(result.get("citations", [])),
                }
            )
    finally:
        db.close()

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "admin_user_id": admin_user_id,
        "total_questions": len(rows),
        "avg_confidence": round(sum(r["confidence"] for r in rows) / max(1, len(rows)), 4),
        "avg_elapsed_seconds": round(sum(r["elapsed_seconds"] for r in rows) / max(1, len(rows)), 4),
        "low_confidence_count": sum(1 for r in rows if r["confidence"] < settings.answer_review_low_confidence),
        "slow_count": sum(1 for r in rows if r["elapsed_seconds"] >= settings.answer_review_slow_seconds),
        "web_fallback_count": sum(1 for r in rows if r["web_fallback_used"]),
    }
    payload = {"summary": summary, "items": rows}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Mini training agent: asks bot selected questions and records outcomes.")
    parser.add_argument("--admin-user-id", type=int, default=0)
    parser.add_argument("--queue-path", default="data/sources/faq_seed_review_queue.json")
    parser.add_argument("--output-path", default="data/processed/mini_agent_training_report.json")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    admin_user_id = args.admin_user_id or _parse_admin_user_id()
    if not admin_user_id:
        raise SystemExit("No admin user id found. Set ADMIN_USER_IDS or pass --admin-user-id.")

    payload = run_training_once(
        admin_user_id=admin_user_id,
        queue_path=Path(args.queue_path),
        output_path=Path(args.output_path),
        limit=max(1, args.limit),
    )
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
