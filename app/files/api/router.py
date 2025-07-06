from fastapi import APIRouter, HTTPException, Header, UploadFile, File, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

from app.files.dependency_injection.container import file_container
from app.authentication.dependency_injection.container import auth_container
from app.files.domain import (
    CreateFileInput,
    MergeFilesInput,
    FileNotFoundError,
    FileNotUploadedError,
    UnauthorizedFileAccessError,
    FileMergeError
)
from app.authentication.domain import InvalidSessionError


router = APIRouter()


class FileInfoRequest(BaseModel):
    name: str
    amount_of_pages: int
    description: Optional[str] = None


class FileResponse(BaseModel):
    file_id: str
    name: str
    pages: int
    uploaded: bool
    description: Optional[str] = None


class CreateFileResponse(BaseModel):
    file_id: str


class MergeRequest(BaseModel):
    file_ids: List[str]


class MergeResponse(BaseModel):
    status: str
    message: str
    merged_file_id: str


async def get_user_external_id(auth_token: str) -> int:
    """Get user external ID from auth token"""
    try:
        user = await auth_container.auth_service.introspect(auth_token)
        return user.external_id
    except InvalidSessionError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )


@router.get("", response_model=dict)
async def get_files(auth: str = Header(alias="Auth")):
    """Get all files owned by the authenticated user"""
    try:
        user_external_id = await get_user_external_id(auth)
        files = await file_container.file_service.get_user_files(user_external_id)
        
        return {
            "status": "ok",
            "files": [
                {
                    "file_id": f.file_id,
                    "name": f.name,
                    "pages": f.amount_of_pages,
                    "uploaded": f.is_uploaded,
                    "description": f.description
                }
                for f in files
            ]
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("", response_model=CreateFileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(file_info: FileInfoRequest, auth: str = Header(alias="Auth")):
    """Create a new file entry"""
    try:
        user_external_id = await get_user_external_id(auth)
        
        input_data = CreateFileInput(
            name=file_info.name,
            amount_of_pages=file_info.amount_of_pages,
            description=file_info.description
        )
        
        file_entity = await file_container.file_service.create_file(input_data, user_external_id)
        
        return CreateFileResponse(file_id=file_entity.file_id)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{file_id}", response_model=dict)
async def get_file(file_id: str, auth: str = Header(alias="Auth")):
    """Get file information and content if available"""
    try:
        user_external_id = await get_user_external_id(auth)
        file_entity = await file_container.file_service.get_file(file_id, user_external_id)
        
        response = {
            "status": "ok",
            "file_id": file_entity.file_id,
            "file_name": file_entity.name,
            "pages": file_entity.amount_of_pages,
            "uploaded": file_entity.is_uploaded,
            "description": file_entity.description
        }
        
        # If file is uploaded and user wants to download, return file
        if file_entity.is_uploaded and file_entity.file_path:
            # You could add a query parameter to trigger download
            # For now, just include info that file is available
            response["download_available"] = True
        
        return response
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedFileAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/{file_id}", response_model=dict)
async def upload_file_content(
    file_id: str, 
    file_content: UploadFile = File(), 
    auth: str = Header(alias="Auth")
):
    """Upload file content"""
    try:
        user_external_id = await get_user_external_id(auth)
        
        # Read file content
        content = await file_content.read()
        
        await file_container.file_service.upload_file_content(
            file_id=file_id,
            owner_external_id=user_external_id,
            file_content=content,
            content_type=file_content.content_type
        )
        
        return {"status": "ok"}
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedFileAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{file_id}", response_model=dict)
async def delete_file(file_id: str, auth: str = Header(alias="Auth")):
    """Delete a file"""
    try:
        user_external_id = await get_user_external_id(auth)
        await file_container.file_service.delete_file(file_id, user_external_id)
        
        return {
            "status": "ok",
            "file_id": file_id,
            "message": "File deleted successfully"
        }
    
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedFileAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/merge", response_model=MergeResponse)
async def merge_files(merge_request: MergeRequest, auth: str = Header(alias="Auth")):
    """Merge multiple PDF files"""
    try:
        user_external_id = await get_user_external_id(auth)
        
        input_data = MergeFilesInput(file_ids=merge_request.file_ids)
        merged_file = await file_container.file_service.merge_files(input_data, user_external_id)
        
        return MergeResponse(
            status="ok",
            message="Files merged successfully",
            merged_file_id=merged_file.file_id
        )
    
    except (FileNotFoundError, FileNotUploadedError, UnauthorizedFileAccessError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if isinstance(e, FileNotFoundError) else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileMergeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )