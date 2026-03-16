import json
import sqlite3
from pathlib import Path

from pipelines.faq_generation.generate_faq import build_usage_faq_candidates


def test_build_usage_faq_candidates(tmp_path: Path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE usage_logs (query TEXT)")
    conn.execute("INSERT INTO usage_logs (query) VALUES (?)", ("Tieu chuan vi sinh cap sach C",))
    conn.execute("INSERT INTO usage_logs (query) VALUES (?)", ("Tieu chuan vi sinh cap sach C",))
    conn.execute("INSERT INTO usage_logs (query) VALUES (?)", ("SOP danh gia nha cung cap",))
    conn.commit()
    conn.close()

    out_path = tmp_path / "faq_candidates.json"
    count = build_usage_faq_candidates(database_path=str(db_path), output_path=str(out_path), limit=10)

    assert count == 2
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload[0]["frequency"] >= payload[1]["frequency"]
    assert "grade c" in payload[0]["question"]
