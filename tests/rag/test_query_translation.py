from core.utils.query_translation import expand_multilingual_query, normalize_query_for_retrieval


def test_expand_multilingual_query_keeps_original_and_focus_terms():
    question = "Tieu chuan vi sinh cap sach C theo Annex 1"
    normalized = normalize_query_for_retrieval(question, "vi")
    queries = expand_multilingual_query(question=question, language="vi", normalized_question=normalized)

    assert queries[0] == question
    assert any("grade c" in q for q in queries)
    assert len(queries) <= 3


def test_normalize_query_for_retrieval_expands_domain_synonyms():
    normalized = normalize_query_for_retrieval("SOP nha cung cap ALCOA+", "vi")
    assert "supplier" in normalized
    assert "alcoa plus data integrity" in normalized
