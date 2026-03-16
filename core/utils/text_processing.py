def normalize_text(text: str) -> str:
    return " ".join(text.split())


def chunk_by_chars(text: str, chunk_size_chars: int = 2800, overlap_chars: int = 400) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap_chars)
    return chunks
