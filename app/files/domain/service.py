from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
import os
from pypdf import PdfMerger
import io

from .entities import FileEntity, CreateFileInput, MergeFilesInput
from .exceptions import (
    FileNotFoundError,
    FileNotUploadedError,
    UnauthorizedFileAccessError,
    FileMergeError
)
from .storage_service import IFileStorageService


class IFileRepository(ABC):
    """Interface for file persistence"""
    
    @abstractmethod
    async def create_file(self, file_data: dict) -> FileEntity:
        pass
    
    @abstractmethod
    async def get_file_by_id(self, file_id: str) -> Optional[FileEntity]:
        pass
    
    @abstractmethod
    async def get_files_by_owner(self, owner_external_id: int) -> List[FileEntity]:
        pass
    
    @abstractmethod
    async def update_file_path(self, file_id: str, file_path: str) -> bool:
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        pass


class FileService:
    """Domain service implementing file management business logic"""
    
    def __init__(self, file_repo: IFileRepository, storage_service: IFileStorageService):
        self.file_repo = file_repo
        self.storage_service = storage_service
    
    async def create_file(self, input_data: CreateFileInput, owner_external_id: int) -> FileEntity:
        """Create a new file entry"""
        file_id = str(uuid.uuid4())
        
        file_data = {
            "file_id": file_id,
            "name": input_data.name,
            "amount_of_pages": input_data.amount_of_pages,
            "description": input_data.description,
            "owner_external_id": owner_external_id
        }
        
        return await self.file_repo.create_file(file_data)
    
    async def get_file(self, file_id: str, owner_external_id: int) -> FileEntity:
        """Get file by ID with ownership check"""
        file_entity = await self.file_repo.get_file_by_id(file_id)
        
        if not file_entity:
            raise FileNotFoundError(f"File {file_id} not found")
        
        if file_entity.owner_external_id != owner_external_id:
            raise UnauthorizedFileAccessError("You don't have access to this file")
        
        return file_entity
    
    async def get_user_files(self, owner_external_id: int) -> List[FileEntity]:
        """Get all files owned by user"""
        return await self.file_repo.get_files_by_owner(owner_external_id)
    
    async def upload_file_content(self, file_id: str, owner_external_id: int, 
                                 file_content: bytes, content_type: str) -> FileEntity:
        """Upload file content"""
        # Check file exists and user owns it
        file_entity = await self.get_file(file_id, owner_external_id)
        
        # Validate content type
        if content_type != "application/pdf":
            raise ValueError(f"Invalid file type: {content_type}. Only PDFs are allowed.")
        
        # Upload to S3
        storage_path = await self.storage_service.upload_file(file_id, file_content)
        
        # Update file path in database
        await self.file_repo.update_file_path(file_id, storage_path)
        file_entity.file_path = storage_path
        file_entity.is_uploaded = True
        
        return file_entity
    
    async def delete_file(self, file_id: str, owner_external_id: int) -> bool:
        """Delete file with ownership check"""
        # Check file exists and user owns it
        file_entity = await self.get_file(file_id, owner_external_id)
        
        # Delete from S3 if uploaded
        if file_entity.is_uploaded:
            await self.storage_service.delete_file(file_id)
        
        # Delete from database
        return await self.file_repo.delete_file(file_id)
    
    async def merge_files(self, input_data: MergeFilesInput, owner_external_id: int) -> FileEntity:
        """Merge multiple PDF files"""
        if len(input_data.file_ids) < 2:
            raise ValueError("At least 2 files are required for merging")
        
        # Check all files exist, are owned by user, and have been uploaded
        files_to_merge = []
        total_pages = 0
        
        for file_id in input_data.file_ids:
            file_entity = await self.get_file(file_id, owner_external_id)
            
            if not file_entity.is_uploaded:
                raise FileNotUploadedError(f"File {file_id} has not been uploaded yet")
            
            # Check if file exists in S3
            if not await self.storage_service.file_exists(file_id):
                raise FileNotFoundError(f"File {file_id} not found in storage")
            
            files_to_merge.append(file_entity)
            total_pages += file_entity.amount_of_pages
        
        # Create merged file entry
        merged_name = f"merged_{'_'.join([f.name[:10] for f in files_to_merge[:3]])}"
        if len(files_to_merge) > 3:
            merged_name += f"_and_{len(files_to_merge)-3}_more"
        
        create_input = CreateFileInput(
            name=merged_name,
            amount_of_pages=total_pages,
            description=f"Merged from {len(files_to_merge)} files"
        )
        
        merged_file = await self.create_file(create_input, owner_external_id)
        
        # Merge PDFs
        try:
            merger = PdfMerger()
            
            # Download files from S3 and merge
            for file_entity in files_to_merge:
                # Download file content from S3
                file_content = await self.storage_service.download_file(file_entity.file_id)
                if not file_content:
                    raise FileNotFoundError(f"Could not download file {file_entity.file_id}")
                
                # Add to merger using BytesIO
                merger.append(io.BytesIO(file_content))
            
            # Write merged PDF to bytes
            merged_bytes = io.BytesIO()
            merger.write(merged_bytes)
            merger.close()
            
            # Upload merged file to S3
            merged_bytes.seek(0)
            storage_path = await self.storage_service.upload_file(
                merged_file.file_id,
                merged_bytes.read()
            )
            
            # Update merged file path in database
            await self.file_repo.update_file_path(merged_file.file_id, storage_path)
            merged_file.file_path = storage_path
            merged_file.is_uploaded = True
            
            return merged_file
            
        except Exception as e:
            # Clean up created file on error
            await self.file_repo.delete_file(merged_file.file_id)
            raise FileMergeError(f"Error merging files: {str(e)}")