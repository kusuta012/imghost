import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi.util import get_ipaddr

from app.db.session import get_db, limiter
from app.models.image import Image
from app.services.storage import storage_service

router = APIRouter(tags=["image_retrieval"])
logger = logging.getLogger("imghost")

@router.get("/i/{filename}")
@limiter.limit("200/minute")
async def get_image(
    filename: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    request
):
    ip_addr = get_ipaddr(request)
    stmt = select(Image).filter(Image.filename == filename)
    result = await db.execute(stmt)
    image = result.scalars().first()
    
    if not image:
        logger.warning(f"Fetch failed: Image not found.", extra={"status": 404, "ip": ip_addr, "filename": filename})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    
    presigned_url = await storage_service.generate_presigned_url(filename)
    
    logger.info(f"Fetch success: Redirecting to signed URL.", extra={"status": 302, "ip": ip_addr, "filename": filename})
    
    response = RedirectResponse(url=presigned_url, status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    
    return response
