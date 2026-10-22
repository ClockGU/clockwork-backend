import os.path
import uuid
from pathlib import Path

from fastapi import UploadFile

from api.env import settings

def upload_file_path(file_name: str) -> Path:
    """
    Generate the full path for the uploaded file.
    """
    return settings.UPLOAD_DIR / file_name

def save_file(file: UploadFile) -> str:
    """
    Save the uploaded file to the specified directory and return the file URL.
    """
    file_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = upload_file_path(file_name)

    if not os.path.isdir(settings.UPLOAD_DIR):
        raise NotADirectoryError("The upload directory does not exist")

    with file_path.open("wb") as f:
        f.write(file.file.read())
    return file_name

def delete_file(file_name: str) -> None:
    """
    Delete the specified file from the upload directory.
    """
    file_path = upload_file_path(file_name)
    if file_path.exists():
        file_path.unlink()
