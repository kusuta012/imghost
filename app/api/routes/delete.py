import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import bcrypt

from app.db.session import get_db
from app.models.image import Image
from app.services.storage import storage_service
from app.core.monitoring import DELETE_COUNT, ERROR_COUNT

router = APIRouter(tags=["image-deletion"])
logger = logging.getLogger("imghost")

@router.delete("/image/{delete_token}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    delete_token: Annotated[str, Path(description="The secret token required to delete the image.")],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    result = await db.execute(select(Image.filename, Image.delete_token_hash))
    hashes_list = result.all()
    
    found_filename = None
    found_hash = None
    token_bytes = delete_token.encode('utf-8')

    for filename, stored_hash_bytes in hashes_list:
         if bcrypt.checkpw(token_bytes, stored_hash_bytes.encode('utf-8')):
                found_filename = filename
                found_hash = stored_hash_bytes
                break
            
    if not found_filename:
        logger.warning(f"Delete failed: Invalid token provided.", extra={"status": 404})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired token")
    
    try:

        await storage_service.delete_file(found_filename)
        await db.execute(delete(Image).where(Image.delete_token_hash == found_hash))
        await db.commit()
        
        DELETE_COUNT.inc()
        logger.info(f"Delete success.", extra={"status": 204, "filename": found_filename})
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        ERROR_COUNT.inc()
        logger.error(f"Delete failed: DB/System error during deletion of {found_filename}: {e}", extra={"status": 500, "filename": found_filename})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during deletion")

    return Response(status_code=status.HTTP_204_NO_CONTENT)