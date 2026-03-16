import argparse
from pathlib import Path

from sentence_transformers import SentenceTransformer


def preload_model(model_name: str, cache_dir: str | None = None) -> None:
    model = SentenceTransformer(model_name, cache_folder=cache_dir, local_files_only=False)
    model.encode(["drug storage temperature", "nhiet do bao quan thuoc"], normalize_embeddings=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Preload embedding model into local cache")
    parser.add_argument("--model", default="BAAI/bge-m3")
    parser.add_argument("--cache-dir", default=None)
    args = parser.parse_args()

    preload_model(model_name=args.model, cache_dir=args.cache_dir)

    cache_root = args.cache_dir or str(Path.home() / ".cache" / "huggingface")
    print(f"Model '{args.model}' cached under: {cache_root}")


if __name__ == "__main__":
    main()
