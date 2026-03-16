import re
import unicodedata

SYNONYMS = {
    "vo trung": "sterile aseptic",
    "san xuat vo trung": "sterile manufacturing aseptic processing",
    "cap sach": "cleanroom grade",
    "kho thuoc": "pharmaceutical warehouse",
    "nhiet do": "temperature",
    "bao quan": "storage",
    "thuoc": "medicinal products",
    "quy dinh": "regulation",
    "duoc": "pharmaceutical",
    "van chuyen": "transport",
    "kiem soat": "control",
    "vi sinh": "microbial",
    "tieu phan": "particle",
    "annex 1": "annex 1 sterile manufacturing",
    "annex1": "annex 1 sterile manufacturing",
    "cap a": "grade a cleanroom",
    "cap b": "grade b cleanroom",
    "cap c": "grade c cleanroom",
    "cap d": "grade d cleanroom",
    "cap sach a": "grade a cleanroom",
    "cap sach b": "grade b cleanroom",
    "cap sach c": "grade c cleanroom",
    "cap sach d": "grade d cleanroom",
    "phong sach": "clean room",
    "tieu chuan": "standard",
    "gioi han": "limit acceptance criteria",
    "tham khao": "recommended reference",
    "mapping": "temperature mapping study",
    "excursion": "temperature excursion deviation",
    "du lieu": "data record",
    "truy vet": "traceability",
    "alcoa": "alcoa data integrity",
    "alcoa+": "alcoa plus data integrity",
    "gdp": "good distribution practice",
    "gxp": "good practices",
    "nha cung cap": "supplier",
    "sop": "standard operating procedure",
}

VI_STOPWORDS = {
    "cac",
    "nhung",
    "ve",
    "trong",
    "la",
    "bao",
    "nhieu",
    "cho",
    "tai",
    "mot",
    "duoc",
    "theo",
    "giua",
    "gom",
    "hay",
    "chi",
    "tiet",
    "nao",
    "khi",
    "can",
}

EN_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "when",
    "what",
    "which",
    "how",
    "are",
    "is",
    "of",
}

COMMON_VI_TYPO_REPLACEMENTS = {
    " nh ": " nha ",
    " cp ": " cap ",
    " cung cp": " cung cap",
    " nh cung": " nha cung",
    "sop nha gi": "sop nha cung cap",
    "sop nh gi nh cung cp": "sop nha cung cap",
    " tieu chuan vi sinh ": " vi sinh gioi han ",
    " tieu chuan nhiet do ": " nhiet do bao quan ",
}

IMPORTANT_PHRASES = (
    "annex 1",
    "grade a",
    "grade b",
    "grade c",
    "grade d",
    "cleanroom",
    "sterile",
    "temperature mapping",
    "data integrity",
    "supplier qualification",
    "change control",
    "capa",
    "alcoa",
    "alcoa+",
    "good distribution practice",
    "good manufacturing practice",
)


def _ascii_lower(text: str) -> str:
    lowered = text.lower().replace("\u0111", "d")
    normalized = unicodedata.normalize("NFD", lowered)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", without_marks).strip()


def normalize_for_matching(text: str) -> str:
    return _ascii_lower(text)


def tokenize_for_matching(text: str) -> list[str]:
    stopwords = VI_STOPWORDS | EN_STOPWORDS
    raw_tokens = re.findall(r"[a-z0-9\+]{2,}", _ascii_lower(text))
    return [token for token in raw_tokens if token not in stopwords]


def remove_vi_stopwords(text: str) -> str:
    words = [w for w in _ascii_lower(text).split() if w not in VI_STOPWORDS]
    return " ".join(words)


def apply_vi_synonyms(text: str) -> str:
    out = _ascii_lower(text)
    out = f" {out} "
    for src, target in COMMON_VI_TYPO_REPLACEMENTS.items():
        out = out.replace(src, target)
    out = re.sub(r"\s+", " ", out).strip()
    placeholders: list[tuple[str, str]] = []
    for idx, (src, target) in enumerate(sorted(SYNONYMS.items(), key=lambda item: len(item[0]), reverse=True)):
        placeholder = f"__syn_{idx}__"
        updated = out.replace(src, placeholder)
        if updated != out:
            placeholders.append((placeholder, target))
            out = updated
    for placeholder, target in placeholders:
        out = out.replace(placeholder, target)
    return out


def _extract_focus_terms(text: str, limit: int = 12) -> str:
    normalized = _ascii_lower(text)
    terms: list[str] = []

    for phrase in IMPORTANT_PHRASES:
        if phrase in normalized:
            terms.append(phrase)

    for token in tokenize_for_matching(normalized):
        if token not in terms:
            terms.append(token)
        if len(terms) >= limit:
            break

    return " ".join(terms[:limit]).strip()


def normalize_query_for_retrieval(question: str, language: str) -> str:
    if language != "vi":
        return normalize_for_matching(question)
    expanded = apply_vi_synonyms(question)
    pruned = remove_vi_stopwords(expanded)
    return pruned.strip()


def expand_multilingual_query(question: str, language: str, normalized_question: str | None = None) -> list[str]:
    normalized = normalized_question or normalize_query_for_retrieval(question, language)
    variants: list[str] = []

    def add(candidate: str) -> None:
        cleaned = candidate.strip()
        if cleaned and cleaned not in variants:
            variants.append(cleaned)

    add(question)
    add(normalized)

    if language == "vi":
        add(apply_vi_synonyms(question))
        focus = _extract_focus_terms(normalized)
        if focus and focus != normalized:
            add(focus)
    else:
        focus = _extract_focus_terms(question)
        if focus and focus != question:
            add(focus)

    return variants[:3]
