from pathlib import Path

from fastapi import UploadFile

from api.env import settings

STUDENT_DOCUMENTS_DIR = "student_documents"
PREV_EMPLOYMENTS_DIR = "prev_employments"


def create_upload_dirs() -> None:
    """
    Create the upload subdirectories if they do not exist.
    """
    for subdir in (STUDENT_DOCUMENTS_DIR, PREV_EMPLOYMENTS_DIR):
        (settings.UPLOAD_DIR / subdir).mkdir(parents=True, exist_ok=True)


def upload_file_path(subdir: str, file_name: str) -> Path:
    """
    Generate the full path for the uploaded file.
    """
    return settings.UPLOAD_DIR / subdir / file_name


def save_file(file: UploadFile, subdir: str, stem: str) -> str:
    """
    Save the uploaded file as `{stem}{ext}` in the given subdirectory and return the file name.
    A previous file with the same stem but a different extension is removed.
    """
    file_name = f"{stem}{Path(file.filename).suffix.lower()}"
    file_path = upload_file_path(subdir, file_name)

    for old_path in file_path.parent.glob(f"{stem}*"):
        if old_path.stem == stem and old_path != file_path:
            old_path.unlink()

    with file_path.open("wb") as f:
        f.write(file.file.read())
    return file_name


def save_student_doc_file(doc, field: str, file: UploadFile) -> str:
    return save_file(file, STUDENT_DOCUMENTS_DIR, f"{doc.id}_{field}")


def save_prev_emp_file(prev_emp, file: UploadFile) -> str:
    return save_file(file, PREV_EMPLOYMENTS_DIR, f"{prev_emp.id}_proof")


def delete_file(subdir: str, file_name: str) -> None:
    """
    Delete the specified file from the given upload subdirectory.
    """
    file_path = upload_file_path(subdir, file_name)
    if file_path.exists():
        file_path.unlink()


def delete_student_doc_file(file_name: str) -> None:
    delete_file(STUDENT_DOCUMENTS_DIR, file_name)


def delete_prev_emp_file(file_name: str) -> None:
    delete_file(PREV_EMPLOYMENTS_DIR, file_name)
