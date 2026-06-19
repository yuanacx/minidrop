"""MinIO upload helper for drop agent."""
from __future__ import annotations

import os
from pathlib import Path

from minio import Minio


def client() -> Minio:
    endpoint = os.environ.get("MINIO_ENDPOINT", "127.0.0.1:9000")
    return Minio(
        endpoint,
        access_key=os.environ.get("MINIO_ROOT_USER", "drop"),
        secret_key=os.environ.get("MINIO_ROOT_PASSWORD", "dropdrop"),
        secure=False,
    )


def upload_file(task_id: str, path: Path, name: str) -> str:
    bucket = os.environ.get("MINIO_BUCKET", "drop")
    c = client()
    if not c.bucket_exists(bucket):
        c.make_bucket(bucket)
    key = f"{task_id}/{name}"
    c.fput_object(bucket, key, str(path))
    return key
