from app.files.domain.service import FileService
from app.files.persistence.repository import FileRepository
from app.files.persistence.s3_storage import S3StorageService


class FileContainer:
    """Dependency injection container for files module"""
    
    _instance = None
    _file_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def file_service(self) -> FileService:
        """Get file service singleton"""
        if self._file_service is None:
            file_repo = FileRepository()
            storage_service = S3StorageService()
            self._file_service = FileService(file_repo, storage_service)
        return self._file_service


# Global instance
file_container = FileContainer()