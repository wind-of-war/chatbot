from core.utils.query_translation import normalize_for_matching, tokenize_for_matching


def _phrase_boost(query_norm: str, text_norm: str) -> int:
    boost = 0
    if query_norm and query_norm in text_norm:
        boost += 8

    important_phrases = (
        "annex 1",
        "grade a",
        "grade b",
        "grade c",
        "grade d",
        "sterile",
        "cleanroom",
        "temperature mapping",
        "supplier qualification",
        "data integrity",
    )
    for phrase in important_phrases:
        if phrase in query_norm and phrase in text_norm:
            boost += 4
    return boost


def lexical_score(query: str, text: str, source: str = "", section: str = "") -> float:
    query_norm = normalize_for_matching(query)
    text_norm = normalize_for_matching(text)
    source_norm = normalize_for_matching(source)
    section_norm = normalize_for_matching(section)

    tokens = tokenize_for_matching(query)
    if not tokens:
        return 0.0

    unique_tokens = list(dict.fromkeys(tokens))
    coverage = sum(1 for token in unique_tokens if token in text_norm)
    exact_token_hits = sum(1 for token in unique_tokens if f" {token} " in f" {text_norm} ")

    score = float(coverage * 2 + exact_token_hits * 1.5)
    score += _phrase_boost(query_norm, text_norm)

    for token in unique_tokens:
        if token in source_norm:
            score += 0.75
        if token in section_norm:
            score += 0.5

    return score
