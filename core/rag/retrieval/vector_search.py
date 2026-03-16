from pathlib import Path

from core.services.vector_store.qdrant_service import QdrantService


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0

    dot = sum(a[i] * b[i] for i in range(n))
    norm_a = sum(a[i] * a[i] for i in range(n)) ** 0.5
    norm_b = sum(b[i] * b[i] for i in range(n)) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _parse_metadata(raw_line: str) -> dict:
    metadata: dict[str, str] = {}
    for part in raw_line.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def _to_int_or_none(raw: str | None) -> int | None:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _local_search(query_vector: list[float], top_k: int, query_language: str) -> list[dict]:
    embeddings_dir = PROJECT_ROOT / "data" / "embeddings"
    processed_dir = PROJECT_ROOT / "data" / "processed"

    if not embeddings_dir.exists() or not processed_dir.exists():
        return []

    scored: list[tuple[float, dict]] = []
    for vec_file in embeddings_dir.glob("*.vec"):
        raw_vec = vec_file.read_text(encoding="utf-8").strip()
        vector = [float(v) for v in raw_vec.split(",") if v]

        txt_file = processed_dir / f"{vec_file.stem}.txt"
        if not txt_file.exists():
            continue

        raw = txt_file.read_text(encoding="utf-8")
        lines = raw.splitlines()
        metadata = _parse_metadata(lines[0]) if lines else {}
        text = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw

        score = _cosine_similarity(query_vector, vector)
        scored.append(
            (
                score,
                {
                    "source": metadata.get("document", txt_file.name),
                    "section": f"chunk-{metadata.get('chunk', vec_file.stem)}",
                    "text": text,
                    "language": metadata.get("language", "en"),
                    "page_start": _to_int_or_none(metadata.get("page_start")),
                    "page_end": _to_int_or_none(metadata.get("page_end")),
                    "query_language": query_language,
                },
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def vector_search(query_vector: list[float], top_k: int = 8, query_language: str = "en") -> list[dict]:
    qdrant_hits = QdrantService().search(query_vector=query_vector, top_k=top_k, query_language=query_language)
    if qdrant_hits:
        return qdrant_hits
    return _local_search(query_vector=query_vector, top_k=top_k, query_language=query_language)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
