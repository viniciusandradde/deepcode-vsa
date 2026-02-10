"""File upload and access routes."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from core.files.service import (
    ALLOWED_MIME_TYPES,
    generate_signed_url,
    upload_file,
    validate_upload,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    thread_id: str | None = Form(None),
    client_id: str | None = Form(None),
    empresa: str | None = Form(None),
):
    try:
        data = await file.read()
        validate_upload(file, data)
        result = upload_file(file, data, thread_id, client_id, empresa)
        signed = generate_signed_url(result["file_id"])
        return {
            "file_id": result["file_id"],
            "name": result["name"],
            "mime": result["mime"],
            "size": result["size"],
            "sha256": result["sha256"],
            "url": signed["url"],
            "expires_at": result["expires_at"],
            "allowed_mime": sorted(ALLOWED_MIME_TYPES),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Upload failed: %s", exc)
        raise HTTPException(status_code=500, detail="Falha ao enviar arquivo")


@router.get("/{file_id}")
async def get_file_signed_url(file_id: str):
    try:
        signed = generate_signed_url(file_id)
        return {
            "url": signed["url"],
            "expires_in": signed["expires_in"],
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Signed URL failed: %s", exc)
        raise HTTPException(status_code=500, detail="Falha ao gerar URL")
