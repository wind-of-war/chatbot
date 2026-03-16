from core.rag.reranker.reranker import rerank


def test_rerank_limits_top_k():
    docs = [{"text": "gdp warehouse temperature control"}, {"text": "random text"}, {"text": "gdp temperature"}]
    out = rerank("temperature gdp", docs, top_k=2)
    assert len(out) == 2


def test_rerank_prioritizes_grade_specific_match():
    docs = [
        {"text": "Grade B microbial monitoring limits for aseptic areas."},
        {"text": "Grade C microbial monitoring limits for cleanroom operations."},
    ]
    out = rerank("cleanroom grade c microbial limits", docs, top_k=1)
    assert out[0]["text"].startswith("Grade C")
