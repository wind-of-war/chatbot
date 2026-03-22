from scripts.mini_training_agent import _build_training_questions


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
