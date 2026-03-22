import json
from pathlib import Path

from core.services.monitoring.training_report import load_mini_training_report


def test_load_mini_training_report(tmp_path: Path):
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps({"summary": {"avg_confidence": 0.8}, "items": [{"question": "q1"}]}),
        encoding="utf-8",
    )
    payload = load_mini_training_report(path=report_path)
    assert payload["summary"]["avg_confidence"] == 0.8
    assert payload["items"][0]["question"] == "q1"
