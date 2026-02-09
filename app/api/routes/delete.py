import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import bcrypt

from app.db.session import get_db
from app.models.image import Image
from app.services.storage import storage_service

router = APIRouter(tags=["image-deletion"])
logger = logging.getLogger("imghost")

@router.delete("/image/{delete_token}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    delete_token: Annotated[str, Path(description="The secret token required to delete the image.")],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    result = await db.execute(select(Image.filename, Image.delete_token_hash))
    hashes = result.all()
    
    found_filename = None
    found_hash = None
    

    for filename, stored_hash_bytes in hashes:
        if stored_hash_bytes and bcrypt.checkpw(delete_token.encode('utf-8'), stored_hash_bytes.encode('utf-8')):
            found_filename = filename
            found_hash = stored_hash_bytes
            break
            
    if not found_filename:
        logger.warning(f"Delete failed: 404 - Invalid token provided")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired token")
    
    try:

        await storage_service.delete_file(found_filename)


        await db.execute(delete(Image).where(Image.delete_token_hash == found_hash))
        await db.commit()
        
        logger.info(f"Delete success: 204 - Filename {found_filename}")
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Delete failed: DB/System error during deletion of {found_filename}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during deletion")

    return Response(status_code=status.HTTP_204_NO_CONTENT)