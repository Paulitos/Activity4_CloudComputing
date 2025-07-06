from fastapi import APIRouter, Header, Body, UploadFile, File, HTTPException
from typing import Union
import httpx
from pydantic import BaseModel
from typing import Optional
import uuid
from pypdf import PdfMerger
import os
from app.files.models import File as FileModel
from app.authentication.models import User

router = APIRouter()

class CarlemanyFile(BaseModel):
    name: str
    amount_of_pages: int
    path: Optional[str] = None


class Person(BaseModel):
    username: str
    mail: str

class FileObjectDatabase(BaseModel):
    id: str
    owner: Person
    file: CarlemanyFile

async def introspect(auth: str) -> Person:
    from app.authentication.models import Session
    session = await Session.filter(token=auth, is_active=True).first()
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = await session.user
    return Person(username=user.username, mail=user.email)

@router.get("")
async def files_get(auth: str = Header(alias="auth")) -> dict[str, Union[str, list]]:
    introspect_response = await introspect(auth=auth)
    
    # Get user from database
    user = await User.filter(username=introspect_response.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Get all files owned by the user
    files = await FileModel.filter(owner_id=user.id).all()
    user_files = []
    for file_obj in files:
        user_files.append({
            "file_id": file_obj.file_id,
            "name": file_obj.name,
            "pages": file_obj.amount_of_pages,
            "uploaded": file_obj.is_uploaded
        })
    
    return {
        "status": "ok",
        "files": user_files
    }


@router.post("")
async def files_post(auth: str = Header(alias="auth"), input_body: CarlemanyFile = Body()) -> dict[str, str]:
    file_id = str(uuid.uuid4())
    introspect_response = await introspect(auth=auth)
    
    # Get user from database
    user = await User.filter(username=introspect_response.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create file in database
    file_obj = await FileModel.create(
        file_id=file_id,
        name=input_body.name,
        amount_of_pages=input_body.amount_of_pages,
        owner_id=user.id
    )
    
    return {
        "file_id": file_obj.file_id,
    }

class MergeContentInput(BaseModel):
    first_id : str
    second_id : str

@router.post("/merge")
async def files_merge(auth: str = Header(alias="auth"), input_body: MergeContentInput = Body()) -> dict[str, str]:
    # Authenticate user
    introspect_response = await introspect(auth=auth)
    user = await User.filter(username=introspect_response.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if both files exist in database
    first_file = await FileModel.filter(file_id=input_body.first_id, owner_id=user.id).first()
    if not first_file:
        raise HTTPException(status_code=404, detail=f"First file {input_body.first_id} not found")
    
    second_file = await FileModel.filter(file_id=input_body.second_id, owner_id=user.id).first()
    if not second_file:
        raise HTTPException(status_code=404, detail=f"Second file {input_body.second_id} not found")
    
    # Check if files have been uploaded
    if not first_file.file_path or not os.path.exists(first_file.file_path):
        raise HTTPException(status_code=400, detail=f"File {input_body.first_id} has not been uploaded yet")
    if not second_file.file_path or not os.path.exists(second_file.file_path):
        raise HTTPException(status_code=400, detail=f"File {input_body.second_id} has not been uploaded yet")
    
    # Merge the PDFs
    merger = PdfMerger()
    try:
        merger.append(first_file.file_path)
        merger.append(second_file.file_path)
        
        # Create new file entry for merged PDF
        merged_id = str(uuid.uuid4())
        merged_path = f"files/{merged_id}.pdf"
        merger.write(merged_path)
        merger.close()
        
        # Calculate total pages
        total_pages = first_file.amount_of_pages + second_file.amount_of_pages
        
        # Create database entry for merged file
        merged_file = await FileModel.create(
            file_id=merged_id,
            name=f"merged_{first_file.name}_{second_file.name}",
            amount_of_pages=total_pages,
            file_path=merged_path,
            is_uploaded=True,
            owner_id=user.id
        )
        
        return {
            "status": "ok",
            "message": "Files merged successfully",
            "merged_file_id": merged_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging files: {str(e)}")


@router.get("/{id}")
async def files_id_get(id: str, auth: str = Header(alias="auth")) -> dict[str, Union[str, int]]:
    # Authenticate user
    introspect_response = await introspect(auth=auth)
    user = await User.filter(username=introspect_response.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if file exists and user owns it
    current_file = await FileModel.filter(file_id=id, owner_id=user.id).first()
    if not current_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "status": "ok",
        "file_id": id,
        "file_name": current_file.name,
        "pages": current_file.amount_of_pages,
        "uploaded": current_file.is_uploaded
    }    

@router.post("/{id}")
async def files_id_post(id: str, file_content: UploadFile = File(), auth: str = Header(alias="auth")) -> dict[str, str]:
    introspect_response = await introspect(auth=auth)
    user = await User.filter(username=introspect_response.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if file exists and user owns it
    current_file = await FileModel.filter(file_id=id, owner_id=user.id).first()
    if not current_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if the file is a PDF
    if file_content.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {file_content.content_type}. Only PDFs are allowed."
        )
    
    # Save file
    filename = id + ".pdf"
    prefix = "files/"
    os.makedirs(prefix, exist_ok=True)
    filepath = prefix + filename
    
    with open(filepath, "wb") as buffer:
        while chunk := await file_content.read(8192):
            buffer.write(chunk)
    
    # Update file in database
    current_file.file_path = filepath
    current_file.is_uploaded = True
    await current_file.save()
    
    return {
        "status": "ok"
    }

@router.delete("/{id}")
async def files_id_delete(id: str, auth: str = Header(alias="auth")) -> dict[str, Union[str, int]]:
    # Authenticate user
    introspect_response = await introspect(auth=auth)
    user = await User.filter(username=introspect_response.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if file exists and user owns it
    current_file = await FileModel.filter(file_id=id, owner_id=user.id).first()
    if not current_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete physical file if it exists
    if current_file.file_path and os.path.exists(current_file.file_path):
        try:
            os.remove(current_file.file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
    
    # Remove from database
    await current_file.delete()
    
    return {
        "status": "ok",
        "file_id": id,
        "message": "File deleted successfully"
    }


