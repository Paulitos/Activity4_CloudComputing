from abc import ABC, abstractmethod
from typing import Optional


class IFileStorageService(ABC):
    """Interface for file storage operations"""
    
    @abstractmethod
    async def upload_file(self, file_id: str, content: bytes) -> str:
        """Upload file content and return the storage path/key"""
        pass
    
    @abstractmethod
    async def download_file(self, file_id: str) -> Optional[bytes]:
        """Download file content"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from storage"""
        pass
    
    @abstractmethod
    async def file_exists(self, file_id: str) -> bool:
        """Check if file exists in storage"""
        pass