from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class FileEntity:
    """Domain entity representing a file"""
    file_id: str
    name: str
    amount_of_pages: int
    owner_external_id: int
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    file_path: Optional[str] = None
    is_uploaded: bool = False
    id: Optional[int] = None


@dataclass
class CreateFileInput:
    """Input for creating a new file"""
    name: str
    amount_of_pages: int
    description: Optional[str] = None


@dataclass
class MergeFilesInput:
    """Input for merging multiple files"""
    file_ids: List[str]