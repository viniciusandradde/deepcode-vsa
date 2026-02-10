"""Image search routes."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.tools.images import search_images

logger = logging.getLogger(__name__)

router = APIRouter()


class ImageSearchRequest(BaseModel):
    query: str = Field(..., max_length=2000)
    limit: int = Field(default=8, ge=1, le=20)
    safe_search: bool = True


@router.post("/search")
async def image_search(request: ImageSearchRequest):
    try:
        results = await search_images(request.query, request.limit, request.safe_search)
        return {"results": results}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Image search failed: %s", exc)
        raise HTTPException(status_code=500, detail="Falha na busca de imagens")
