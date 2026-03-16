from datetime import datetime

from core.utils.language_detection import detect_language


def enrich_metadata(
    document_name: str,
    chunk_index: int,
    content: str,
    page_start: int | None = None,
    page_end: int | None = None,
) -> str:
    language = detect_language(content)
    page_start_str = str(page_start) if page_start is not None else ""
    page_end_str = str(page_end) if page_end is not None else ""
    return (
        f"document={document_name};chunk={chunk_index};chars={len(content)};"
        f"language={language};page_start={page_start_str};page_end={page_end_str};"
        f"indexed_at={datetime.utcnow().isoformat()}"
    )
