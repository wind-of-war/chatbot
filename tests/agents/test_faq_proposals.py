import json
from pathlib import Path

from scripts.build_faq_proposals import build_proposals


def test_build_proposals_deduplicates_seed(tmp_path: Path):
    review_log = tmp_path / "review.jsonl"
    faq_seed = tmp_path / "faq_seed.json"
    out_json = tmp_path / "proposals.json"
    out_md = tmp_path / "proposals.md"

    faq_seed.write_text(
        json.dumps(
            [
                {
                    "id": "seed_1",
                    "language": "vi",
                    "question_patterns": ["tieu chuan vi sinh cap sach c"],
                    "answer": "seed",
                    "section": "seed",
                }
            ]
        ),
        encoding="utf-8",
    )
    review_log.write_text(
        "\n".join(
            [
                json.dumps({"question": "tieu chuan vi sinh cap sach C", "confidence": 0.9, "elapsed_seconds": 2}),
                json.dumps({"question": "deviation va capa la gi", "confidence": 0.2, "elapsed_seconds": 20}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proposals = build_proposals(
        review_log_path=review_log,
        faq_seed_path=faq_seed,
        output_json_path=out_json,
        output_md_path=out_md,
        top_k=10,
        slow_threshold=12.0,
        low_conf_threshold=0.55,
    )

    assert len(proposals) == 1
    assert "deviation" in proposals[0]["normalized_question"]
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert len(payload) == 1
