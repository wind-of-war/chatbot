from pathlib import Path

from configs.settings import settings


class S3Service:
    """Local stub for S3 interface. Writes into `data/raw` for dev."""

    def upload(self, local_path: str, key: str) -> str:
        target = Path("data/raw") / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(local_path).read_bytes())
        return f"s3://{settings.s3_bucket}/{key}"
