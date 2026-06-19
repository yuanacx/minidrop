#!/usr/bin/env python3
"""MinIO storage helper for analysis pipeline."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from minio import Minio


def client_from_env() -> Minio:
    endpoint = os.environ.get("S3_ENDPOINT", "localhost:9000")
    secure = os.environ.get("S3_SECURE", "false").lower() == "true"
    return Minio(
        endpoint,
        access_key=os.environ.get("MINIO_ROOT_USER", "drop"),
        secret_key=os.environ.get("MINIO_ROOT_PASSWORD", "dropdrop"),
        secure=secure,
    )


def download_object(bucket: str, key: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    client_from_env().fget_object(bucket, key, str(dest))
    return dest


def upload_file(bucket: str, key: str, path: Path, content_type: str = "application/octet-stream") -> str:
    client = client_from_env()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    client.fput_object(bucket, key, str(path), content_type=content_type)
    return key
