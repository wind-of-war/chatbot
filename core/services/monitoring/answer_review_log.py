from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from configs.settings import settings


def append_answer_review_event(event: dict) -> None:
    path = Path(settings.answer_review_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_answer_review_events(limit: int = 50) -> list[dict]:
    path = Path(settings.answer_review_log_path)
    if not path.exists():
        return []
    rows = path.read_text(encoding="utf-8").splitlines()
    events: list[dict] = []
    for line in rows[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))
