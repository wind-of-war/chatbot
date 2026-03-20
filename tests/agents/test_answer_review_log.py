from core.services.monitoring.answer_review_log import append_answer_review_event, load_answer_review_events


def test_answer_review_log_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("configs.settings.settings.answer_review_log_path", str(tmp_path / "review.jsonl"))
    append_answer_review_event({"question": "test", "confidence": 0.2})
    append_answer_review_event({"question": "test 2", "confidence": 0.9})

    events = load_answer_review_events(limit=10)
    assert len(events) == 2
    assert events[0]["question"] == "test 2"
    assert events[1]["question"] == "test"
