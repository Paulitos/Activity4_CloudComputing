class FileError(Exception):
    """Base exception for file-related errors"""
    pass


class FileNotFoundError(FileError):
    """Raised when file is not found"""
    pass


class FileNotUploadedError(FileError):
    """Raised when trying to access file content that hasn't been uploaded"""
    pass


class UnauthorizedFileAccessError(FileError):
    """Raised when user tries to access a file they don't own"""
    pass


class FileMergeError(FileError):
    """Raised when file merge operation fails"""
    pass