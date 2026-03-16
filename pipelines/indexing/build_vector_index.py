import hashlib
from pathlib import Path

from core.services.embedding_service.embedder import Embedder
from core.services.vector_store.qdrant_service import QdrantService


EMBED_BATCH_SIZE = 64
UPSERT_BATCH_SIZE = 256


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


def _build_point(metadata: dict, text_file: Path, chunk_text: str, vector: list[float]) -> dict:
    source = metadata.get("document", text_file.name)
    section = f"chunk-{metadata.get('chunk', text_file.stem)}"
    page_start = _to_int_or_none(metadata.get("page_start"))
    page_end = _to_int_or_none(metadata.get("page_end"))
    point_id = hashlib.md5(f"{source}|{section}".encode("utf-8")).hexdigest()
    return {
        "id": point_id,
        "vector": vector,
        "source": source,
        "section": section,
        "text": chunk_text,
        "language": metadata.get("language", "en"),
        "page_start": page_start,
        "page_end": page_end,
    }


def _flush_embeddings(embedder: Embedder, pending: list[dict]) -> None:
    if not pending:
        return
    vectors = embedder.embed_many([p["chunk_text"] for p in pending], batch_size=EMBED_BATCH_SIZE)
    for item, vec in zip(pending, vectors):
        item["vector"] = vec
        item["out_file"].write_text(",".join(f"{v:.6f}" for v in vec), encoding="utf-8")


def build_vector_index(processed_dir: str) -> int:
    embedder = Embedder()
    qdrant = QdrantService()

    embedding_dir = Path("data/embeddings")
    embedding_dir.mkdir(parents=True, exist_ok=True)

    upsert_buffer: list[dict] = []
    pending_embed: list[dict] = []
    upserted_total = 0

    text_files = sorted(Path(processed_dir).glob("*.txt"))

    def flush_upsert() -> None:
        nonlocal upserted_total
        if not upsert_buffer:
            return
        upserted_total += qdrant.upsert_documents(upsert_buffer)
        upsert_buffer.clear()

    for idx, text_file in enumerate(text_files, start=1):
        raw = text_file.read_text(encoding="utf-8")
        lines = raw.splitlines()
        metadata = _parse_metadata(lines[0]) if lines else {}
        chunk_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw

        out_file = embedding_dir / f"{text_file.stem}.vec"
        if out_file.exists() and out_file.stat().st_mtime >= text_file.stat().st_mtime:
            raw_vec = out_file.read_text(encoding="utf-8").strip()
            vector = [float(v) for v in raw_vec.split(",") if v]
            upsert_buffer.append(_build_point(metadata, text_file, chunk_text, vector))
        else:
            pending_embed.append(
                {
                    "metadata": metadata,
                    "text_file": text_file,
                    "chunk_text": chunk_text,
                    "out_file": out_file,
                }
            )

        if len(pending_embed) >= EMBED_BATCH_SIZE:
            _flush_embeddings(embedder, pending_embed)
            for item in pending_embed:
                upsert_buffer.append(_build_point(item["metadata"], item["text_file"], item["chunk_text"], item["vector"]))
            pending_embed.clear()

        if len(upsert_buffer) >= UPSERT_BATCH_SIZE:
            flush_upsert()

        if idx % 2000 == 0:
            print(f"[index] scanned={idx}/{len(text_files)} upserted={upserted_total} pending={len(upsert_buffer)}")

    if pending_embed:
        _flush_embeddings(embedder, pending_embed)
        for item in pending_embed:
            upsert_buffer.append(_build_point(item["metadata"], item["text_file"], item["chunk_text"], item["vector"]))
        pending_embed.clear()

    try:
        flush_upsert()
        return upserted_total
    except Exception as exc:
        print(f"[WARN] Qdrant unavailable, vectors saved locally only: {exc}")
        return 0


if __name__ == "__main__":
    count = build_vector_index("data/processed")
    print(f"Built {count} vectors")
