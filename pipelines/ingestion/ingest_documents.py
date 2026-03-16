import argparse
import json
from bisect import bisect_left
from pathlib import Path

import fitz

from core.utils.text_processing import normalize_text
from pipelines.ingestion.metadata_enrichment import enrich_metadata


def _build_text_and_page_spans(doc: fitz.Document) -> tuple[str, list[tuple[int, int, int]]]:
    page_texts: list[str] = []
    page_spans: list[tuple[int, int, int]] = []
    cursor = 0

    for i, page in enumerate(doc, start=1):
        normalized = normalize_text(page.get_text("text") or "")
        if not normalized:
            continue
        if page_texts:
            cursor += 1
        start = cursor
        end = start + len(normalized)
        page_texts.append(normalized)
        page_spans.append((start, end, i))
        cursor = end

    return "\n".join(page_texts), page_spans


def _page_for_offset(page_spans: list[tuple[int, int, int]], offset: int) -> int | None:
    if not page_spans:
        return None
    starts = [s for s, _, _ in page_spans]
    idx = bisect_left(starts, max(0, offset))
    if idx >= len(page_spans):
        idx = len(page_spans) - 1
    if idx > 0 and page_spans[idx][0] > offset:
        idx -= 1
    return page_spans[idx][2]


def _chunk_with_offsets(text: str, chunk_size_chars: int = 2800, overlap_chars: int = 400) -> list[tuple[int, int, str]]:
    chunks: list[tuple[int, int, str]] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((start, end, chunk))
        if end == len(text):
            break
        start = max(0, end - overlap_chars)
    return chunks


def _load_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def ingest_documents(raw_dir: str) -> int:
    raw_path = Path(raw_dir)
    processed_path = Path("data/processed")
    processed_path.mkdir(parents=True, exist_ok=True)

    state_file = processed_path / ".ingest_state.json"
    prev_state = _load_state(state_file)
    next_state: dict[str, dict] = {}

    total_chunks = 0
    failed_files = 0
    skipped_files = 0

    for pdf in sorted(raw_path.rglob("*.pdf")):
        rel_pdf = str(pdf.relative_to(raw_path)).replace("\\", "/")
        stat = pdf.stat()
        sig = {"mtime": int(stat.st_mtime), "size": int(stat.st_size)}
        prev_sig = prev_state.get(rel_pdf)

        rel_stem = pdf.relative_to(raw_path).with_suffix("")
        safe_stem = str(rel_stem).replace("\\", "__").replace("/", "__")

        if prev_sig == sig:
            skipped_files += 1
            next_state[rel_pdf] = sig
            continue

        try:
            with fitz.open(pdf) as doc:
                text, page_spans = _build_text_and_page_spans(doc)
        except Exception as exc:
            failed_files += 1
            print(f"[WARN] Skip unreadable PDF: {pdf.name} ({exc})")
            continue

        if not text.strip():
            next_state[rel_pdf] = sig
            continue

        chunks = _chunk_with_offsets(text)

        for idx, (start_off, end_off, chunk) in enumerate(chunks, start=1):
            page_start = _page_for_offset(page_spans, start_off)
            page_end = _page_for_offset(page_spans, max(start_off, end_off - 1))
            metadata = enrich_metadata(
                document_name=pdf.name,
                chunk_index=idx,
                content=chunk,
                page_start=page_start,
                page_end=page_end,
            )
            out_file = processed_path / f"{safe_stem}_chunk_{idx}.txt"
            payload = f"{metadata}\n{chunk}"
            if out_file.exists() and out_file.read_text(encoding="utf-8") == payload:
                total_chunks += 1
                continue
            out_file.write_text(payload, encoding="utf-8")
            total_chunks += 1

        next_state[rel_pdf] = sig

    _save_state(state_file, next_state)

    if failed_files:
        print(f"[WARN] Failed files: {failed_files}")
    if skipped_files:
        print(f"[INFO] Skipped unchanged files: {skipped_files}")

    return total_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDF documents into processed chunks")
    parser.add_argument("--raw-dir", default="data/raw", help="Root directory containing PDF files")
    args = parser.parse_args()

    count = ingest_documents(args.raw_dir)
    print(f"Ingested {count} chunks")
