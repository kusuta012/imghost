import boto3
import asyncio
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status
from typing import BinaryIO
from app.core.config import settings

class StorageService:
    def __init__(self):
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            region_name='ap-mumbai-1',
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        
    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        mime_type: str
    ) -> str:
        
        try:
            
            await asyncio.to_thread(
                self.s3_client.upload_fileobj,
                file_obj,
                self.bucket_name,
                filename,
                ExtraArgs={'ContentType': mime_type}
            )
            
            object_url = f"{settings.S3_ENDPOINT_URL}/{self.bucket_name}/{filename}"
            return object_url
        
        except (BotoCoreError, ClientError) as e:
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not upload file to storagee"
            )
            
    async def generate_presigned_url(self, filename: str) -> str:
        try:
            url = await asyncio.to_thread(
                self.s3_client.generate_presigned_url,
                ClientMethod='get_object',
                Params={'Bucket': self.bucket_name, 'Key': filename},
                ExpiresIn=settings.PRESIGNED_URL_EXPIRY_SECONDS
            )
            return url
        except (BotoCoreError, ClientError) as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate signed url"
            )
            
    async def delete_file(self, filename: str) -> None:
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=filename
            )
        except (BotoCoreError, ClientError) as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not detail file from storage"
            )
            
            
            
            
storage_service = StorageService()