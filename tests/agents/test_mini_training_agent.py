import json
from pathlib import Path

from scripts.mini_training_agent import _build_training_questions
from scripts.mini_training_agent import append_weak_items_to_review_queue


def test_build_training_questions_prioritizes_queue():
    queue = [
        "Q1 from queue",
        "Q2 from queue",
    ]
    out = _build_training_questions(limit=3, queue_questions=queue)
    assert out[0] == "Q1 from queue"
    assert out[1] == "Q2 from queue"
    assert len(out) == 3


def test_build_training_questions_deduplicates():
    queue = ["Tieu chuan vi sinh cap sach C", "Tieu chuan vi sinh cap sach C"]
    out = _build_training_questions(limit=5, queue_questions=queue)
    assert out.count("Tieu chuan vi sinh cap sach C") == 1


def test_append_weak_items_to_review_queue(tmp_path: Path):
    payload = {
        "items": [
            {
                "question": "Temperature excursion trong kho duoc xu ly nhu the nao?",
                "confidence": 0.45,
                "elapsed_seconds": 40.0,
                "web_fallback_used": False,
            },
            {
                "question": "ALCOA+ trong GMP duoc ap dung the nao?",
                "confidence": 0.92,
                "elapsed_seconds": 0.5,
                "web_fallback_used": False,
            },
        ]
    }
    queue = tmp_path / "queue.json"
    added = append_weak_items_to_review_queue(
        payload=payload,
        queue_path=queue,
        slow_threshold=12.0,
        low_conf_threshold=0.55,
    )
    assert added == 1
    data = json.loads(queue.read_text(encoding="utf-8"))
    assert len(data) == 1
