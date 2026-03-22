from __future__ import annotations

import json
from pathlib import Path


DEFAULT_REPORT_PATH = Path("data/processed/mini_agent_training_report.json")


def load_mini_training_report(path: Path = DEFAULT_REPORT_PATH) -> dict:
    if not path.exists():
        return {"summary": None, "items": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"summary": None, "items": []}
    if not isinstance(payload, dict):
        return {"summary": None, "items": []}
    return {
        "summary": payload.get("summary"),
        "items": payload.get("items", []),
    }
