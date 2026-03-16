from core.utils.text_processing import chunk_by_chars


def chunking(text: str) -> list[str]:
    return chunk_by_chars(text)
