"""File storage service for uploads and retrieval."""

from __future__ import annotations

import hashlib
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable

from fastapi import UploadFile

from core.config import get_settings
from core.database import get_conn
from core.storage.minio_client import ensure_bucket_exists, get_minio_client, get_public_endpoint
from core.files.extractors import (
    extract_text_from_csv,
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_from_txt,
)

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/csv",
    "image/png",
    "image/jpeg",
}

MAX_EXTRACT_CHARS = 12000


def _max_size_bytes() -> int:
    settings = get_settings()
    return settings.files_max_size_mb * 1024 * 1024


def _expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=30)


def _compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sanitize_filename(name: str) -> str:
    safe = name.replace("\\", "/").split("/")[-1]
    return safe[:180] or "file"


def _build_object_key(thread_id: str | None, filename: str) -> str:
    prefix = thread_id or "general"
    uid = uuid.uuid4().hex
    return f"{prefix}/{uid}-{filename}"


def validate_upload(file: UploadFile, data: bytes) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Tipo de arquivo não suportado")
    if len(data) > _max_size_bytes():
        raise ValueError("Arquivo excede o limite de 4MB")


def upload_file(
    file: UploadFile,
    data: bytes,
    thread_id: str | None,
    client_id: str | None,
    empresa: str | None,
) -> dict:
    settings = get_settings()
    ensure_bucket_exists(settings.minio_bucket)

    filename = _sanitize_filename(file.filename or "file")
    object_key = _build_object_key(thread_id, filename)
    sha256 = _compute_sha256(data)
    size = len(data)

    client = get_minio_client()
    client.put_object(
        settings.minio_bucket,
        object_key,
        io.BytesIO(data),
        length=size,
        content_type=file.content_type,
    )

    file_id = f"file_{uuid.uuid4().hex}"
    expires_at = _expires_at()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO files (
                    id, thread_id, client_id, empresa, name, mime, size, sha256,
                    bucket, object_key, created_at, expires_at, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), %s, 'active')
                """,
                (
                    file_id,
                    thread_id,
                    client_id,
                    empresa,
                    filename,
                    file.content_type,
                    size,
                    sha256,
                    settings.minio_bucket,
                    object_key,
                    expires_at,
                ),
            )
        conn.commit()

    return {
        "file_id": file_id,
        "name": filename,
        "mime": file.content_type,
        "size": size,
        "sha256": sha256,
        "bucket": settings.minio_bucket,
        "object_key": object_key,
        "expires_at": expires_at.isoformat(),
    }


def _get_file_record(file_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, mime, size, sha256, bucket, object_key, expires_at, status
                FROM files
                WHERE id = %s
                """,
                (file_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "mime": row[2],
        "size": row[3],
        "sha256": row[4],
        "bucket": row[5],
        "object_key": row[6],
        "expires_at": row[7],
        "status": row[8],
    }


def generate_signed_url(file_id: str) -> dict:
    settings = get_settings()
    record = _get_file_record(file_id)
    if not record or record["status"] != "active":
        raise ValueError("Arquivo não encontrado")

    client = get_minio_client()
    url = client.presigned_get_object(
        record["bucket"],
        record["object_key"],
        expires=timedelta(seconds=settings.signed_url_ttl_seconds),
    )

    public_endpoint = get_public_endpoint()
    if public_endpoint:
        endpoint = public_endpoint.rstrip("/")
        internal_endpoint = settings.minio_endpoint.rstrip("/") if settings.minio_endpoint else ""
        if internal_endpoint and not internal_endpoint.startswith("http"):
            internal_endpoint = f"http://{internal_endpoint}"
        if internal_endpoint and url.startswith(internal_endpoint):
            url = endpoint + url[len(internal_endpoint) :]

    return {
        "url": url,
        "expires_in": settings.signed_url_ttl_seconds,
        "record": record,
    }


def download_file_bytes(file_id: str) -> tuple[dict, bytes]:
    record = _get_file_record(file_id)
    if not record or record["status"] != "active":
        raise ValueError("Arquivo não encontrado")

    client = get_minio_client()
    obj = client.get_object(record["bucket"], record["object_key"])
    try:
        data = obj.read()
    finally:
        obj.close()
        obj.release_conn()
    return record, data


def extract_text_from_file(file_id: str) -> str:
    record, data = download_file_bytes(file_id)
    mime = record["mime"]
    if mime == "application/pdf":
        text = extract_text_from_pdf(data)
    elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_docx(data)
    elif mime == "text/plain":
        text = extract_text_from_txt(data)
    elif mime == "text/csv":
        text = extract_text_from_csv(data)
    else:
        return ""

    if len(text) > MAX_EXTRACT_CHARS:
        text = text[:MAX_EXTRACT_CHARS] + "\n\n[conteudo truncado]"
    return text.strip()


def cleanup_expired_files(limit: int = 200) -> dict:
    settings = get_settings()
    client = get_minio_client()
    removed = 0
    failed: list[str] = []

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, bucket, object_key
                FROM files
                WHERE expires_at <= now()
                  AND status = 'active'
                ORDER BY expires_at ASC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

        for file_id, bucket, object_key in rows:
            try:
                client.remove_object(bucket, object_key)
                removed += 1
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE files SET status = 'deleted' WHERE id = %s",
                        (file_id,),
                    )
            except Exception as exc:
                failed.append(file_id)
                logger.warning("Failed to delete file %s: %s", file_id, exc)

        conn.commit()

    return {"removed": removed, "failed": failed, "limit": limit}


def summarize_attachments(file_ids: Iterable[str]) -> list[dict]:
    summaries = []
    for file_id in file_ids:
        record = _get_file_record(file_id)
        if record:
            summaries.append(
                {
                    "file_id": record["id"],
                    "name": record["name"],
                    "mime": record["mime"],
                    "size": record["size"],
                }
            )
    return summaries
