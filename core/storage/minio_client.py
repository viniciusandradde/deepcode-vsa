"""MinIO client helper utilities."""

from __future__ import annotations

import logging
from functools import lru_cache
from urllib.parse import urlparse

from minio import Minio

from core.config import get_settings

logger = logging.getLogger(__name__)


def _normalize_endpoint(endpoint: str) -> tuple[str, bool]:
    parsed = urlparse(endpoint)
    if parsed.scheme in ("http", "https"):
        return parsed.netloc, parsed.scheme == "https"
    return endpoint, False


@lru_cache
def get_minio_client() -> Minio:
    settings = get_settings()
    if not settings.minio_endpoint:
        raise RuntimeError("MINIO_ENDPOINT is not configured")

    endpoint, secure = _normalize_endpoint(settings.minio_endpoint)
    client = Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )
    return client


def ensure_bucket_exists(bucket: str) -> None:
    client = get_minio_client()
    found = client.bucket_exists(bucket)
    if not found:
        client.make_bucket(bucket)
        logger.info("Created MinIO bucket: %s", bucket)


def get_public_endpoint() -> str:
    settings = get_settings()
    return settings.minio_public_endpoint or settings.minio_endpoint
