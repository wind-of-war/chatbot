import argparse
import json
import ssl
import urllib.request
from pathlib import Path


def _download_file(url: str, out_path: Path, timeout: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "gxp-ai-platform/1.0 (+document-sync)",
            "Accept": "application/pdf,*/*",
        },
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
        payload = response.read()

    # Basic integrity guard to avoid saving HTML error pages as PDF files.
    if len(payload) < 4096 or not payload.startswith(b"%PDF"):
        raise ValueError("Downloaded content is not a valid PDF payload")

    out_path.write_bytes(payload)


def download_from_manifest(manifest_path: Path, raw_root: Path, force: bool, timeout: int) -> tuple[int, int, int]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = data.get("sources", [])
    downloaded = 0
    skipped = 0
    failed = 0

    for src in sources:
        if not src.get("enabled", True):
            continue
        if src.get("manual_only"):
            category = src.get("category", "manual")
            folder = raw_root / category
            folder.mkdir(parents=True, exist_ok=True)
            note = src.get("notes", "Manual upload required.")
            note_file = folder / "README_manual_upload.txt"
            if not note_file.exists():
                note_file.write_text(note + "\n", encoding="utf-8")
            skipped += 1
            print(f"MANUAL {src.get('id')}: {note}")
            continue

        url = src.get("url", "").strip()
        filename = src.get("filename", "").strip()
        if not url or not filename:
            failed += 1
            print(f"FAIL {src.get('id')}: missing url/filename")
            continue

        category = src.get("category", "misc")
        out_path = raw_root / category / filename
        if out_path.exists() and not force:
            skipped += 1
            print(f"SKIP {src.get('id')}: {out_path}")
            continue

        try:
            _download_file(url, out_path, timeout=timeout)
            downloaded += 1
            print(f"OK {src.get('id')}: {out_path}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {src.get('id')}: {exc}")

    return downloaded, skipped, failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download regulatory PDF sources into data/raw")
    parser.add_argument(
        "--manifest",
        default="data/sources/regulatory_docs_sources.json",
        help="Path to source manifest JSON",
    )
    parser.add_argument("--raw-root", default="data/raw", help="Root path for downloaded files")
    parser.add_argument("--force", action="store_true", help="Re-download existing files")
    parser.add_argument("--timeout", type=int, default=180, help="HTTP timeout seconds")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    raw_root = Path(args.raw_root)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    downloaded, skipped, failed = download_from_manifest(manifest_path, raw_root, args.force, args.timeout)
    print(f"Summary: downloaded={downloaded}, skipped={skipped}, failed={failed}")
