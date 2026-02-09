import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.image import Image
from app.services.storage import storage_service

router = APIRouter(tags=["image_retrieval"])
logger = logging.getLogger("imghost")

@router.get("/i/{filename}")
async def get_image(
    filename: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    
    stmt = select(Image).filter(Image.filename == filename)
    result = await db.execute(stmt)
    image = result.scalars().first()
    
    if not image:
        logger.warning(f"Fetch failed: 404 - Filename {filename} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    
    presigned_url = await storage_service.generate_presigned_url(filename)
    
    logger.info(f"Fetch sucess: 302 - Filname {filename}")
    
    response = RedirectResponse(url=presigned_url, status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    
    return response
