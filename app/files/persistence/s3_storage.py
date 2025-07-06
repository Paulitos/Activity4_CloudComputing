import os
import boto3
from typing import Optional
from botocore.exceptions import ClientError

from app.files.domain.storage_service import IFileStorageService


class S3StorageService(IFileStorageService):
    """S3 implementation of file storage"""
    
    def __init__(self):
        self._s3_client = None
        self._bucket_name = os.getenv("S3_BUCKET_NAME", "carlemany-files")
        self._endpoint_url = os.getenv("AWS_ENDPOINT_URL")  # For LocalStack
        self._region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    async def _get_s3_client(self):
        """Get S3 client (lazy initialization)"""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                endpoint_url=self._endpoint_url,
                region_name=self._region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test")
            )
            
            # Create bucket if it doesn't exist (for LocalStack)
            try:
                self._s3_client.head_bucket(Bucket=self._bucket_name)
            except ClientError:
                self._s3_client.create_bucket(Bucket=self._bucket_name)
        
        return self._s3_client
    
    async def upload_file(self, file_id: str, content: bytes) -> str:
        """Upload file content to S3"""
        s3_client = await self._get_s3_client()
        key = f"files/{file_id}.pdf"
        
        try:
            s3_client.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=content,
                ContentType='application/pdf'
            )
            return key
        except Exception as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    async def download_file(self, file_id: str) -> Optional[bytes]:
        """Download file content from S3"""
        s3_client = await self._get_s3_client()
        key = f"files/{file_id}.pdf"
        
        try:
            response = s3_client.get_object(
                Bucket=self._bucket_name,
                Key=key
            )
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise Exception(f"Failed to download file from S3: {str(e)}")
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from S3"""
        s3_client = await self._get_s3_client()
        key = f"files/{file_id}.pdf"
        
        try:
            s3_client.delete_object(
                Bucket=self._bucket_name,
                Key=key
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file from S3: {str(e)}")
    
    async def file_exists(self, file_id: str) -> bool:
        """Check if file exists in S3"""
        s3_client = await self._get_s3_client()
        key = f"files/{file_id}.pdf"
        
        try:
            s3_client.head_object(
                Bucket=self._bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise Exception(f"Failed to check file existence in S3: {str(e)}")