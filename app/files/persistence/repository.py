from typing import Optional, List

from app.files.models import File
from app.files.domain.entities import FileEntity
from app.files.domain.service import IFileRepository
from app.authentication.models import User


class FileRepository(IFileRepository):
    """Tortoise ORM implementation of file repository"""
    
    async def create_file(self, file_data: dict) -> FileEntity:
        """Create a new file"""
        # Get user by external_id
        user = await User.filter(external_id=file_data["owner_external_id"]).first()
        if not user:
            raise ValueError(f"User with external_id {file_data['owner_external_id']} not found")
        
        file = await File.create(
            file_id=file_data["file_id"],
            name=file_data["name"],
            amount_of_pages=file_data["amount_of_pages"],
            description=file_data.get("description"),
            owner_id=user.id
        )
        
        return FileEntity(
            id=file.id,
            file_id=file.file_id,
            name=file.name,
            amount_of_pages=file.amount_of_pages,
            description=file.description,
            file_path=file.file_path,
            is_uploaded=file.is_uploaded,
            owner_external_id=user.external_id,
            created_at=file.created_at,
            updated_at=file.updated_at
        )
    
    async def get_file_by_id(self, file_id: str) -> Optional[FileEntity]:
        """Get file by ID"""
        file = await File.filter(file_id=file_id).first()
        if not file:
            return None
        
        # Get owner
        owner = await file.owner
        
        return FileEntity(
            id=file.id,
            file_id=file.file_id,
            name=file.name,
            amount_of_pages=file.amount_of_pages,
            description=file.description,
            file_path=file.file_path,
            is_uploaded=file.is_uploaded,
            owner_external_id=owner.external_id,
            created_at=file.created_at,
            updated_at=file.updated_at
        )
    
    async def get_files_by_owner(self, owner_external_id: int) -> List[FileEntity]:
        """Get all files owned by user"""
        # Get user by external_id
        user = await User.filter(external_id=owner_external_id).first()
        if not user:
            return []
        
        files = await File.filter(owner_id=user.id).all()
        
        return [
            FileEntity(
                id=file.id,
                file_id=file.file_id,
                name=file.name,
                amount_of_pages=file.amount_of_pages,
                description=file.description,
                file_path=file.file_path,
                is_uploaded=file.is_uploaded,
                owner_external_id=owner_external_id,
                created_at=file.created_at,
                updated_at=file.updated_at
            )
            for file in files
        ]
    
    async def update_file_path(self, file_id: str, file_path: str) -> bool:
        """Update file path"""
        file = await File.filter(file_id=file_id).first()
        if not file:
            return False
        
        file.file_path = file_path
        file.is_uploaded = True
        await file.save()
        return True
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file"""
        file = await File.filter(file_id=file_id).first()
        if not file:
            return False
        
        await file.delete()
        return True