import io
import uuid
from types import SimpleNamespace

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient

from api.env import settings
from api.utils import (
    PREV_EMPLOYMENTS_DIR,
    STUDENT_DOCUMENTS_DIR,
    create_upload_dirs,
    delete_file,
    save_prev_emp_file,
    save_student_doc_file,
    upload_file_path,
)


def make_upload(filename, content=b"content"):
    return UploadFile(file=io.BytesIO(content), filename=filename)


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    create_upload_dirs()
    return tmp_path


@pytest.fixture
def doc():
    return SimpleNamespace(id=uuid.uuid4())


def test_create_upload_dirs_creates_subdirs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path / "uploads")
    create_upload_dirs()
    create_upload_dirs()  # idempotent
    assert (tmp_path / "uploads" / STUDENT_DOCUMENTS_DIR).is_dir()
    assert (tmp_path / "uploads" / PREV_EMPLOYMENTS_DIR).is_dir()


def test_app_startup_creates_subdirs(tmp_path, monkeypatch):
    from api.main import app

    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path / "uploads")
    with TestClient(app):
        pass
    assert (tmp_path / "uploads" / STUDENT_DOCUMENTS_DIR).is_dir()
    assert (tmp_path / "uploads" / PREV_EMPLOYMENTS_DIR).is_dir()


def test_save_student_doc_file_location_and_return_value(upload_dir, doc):
    file_name = save_student_doc_file(doc, "elstam", make_upload("my scan.pdf"))

    assert file_name == f"{doc.id}_elstam.pdf"
    stored = upload_dir / STUDENT_DOCUMENTS_DIR / file_name
    assert stored.read_bytes() == b"content"
    assert upload_file_path(STUDENT_DOCUMENTS_DIR, file_name) == stored


def test_uppercase_extension_is_lowercased(upload_dir, doc):
    file_name = save_student_doc_file(doc, "elstam", make_upload("SCAN.PDF"))
    assert file_name == f"{doc.id}_elstam.pdf"


def test_no_extension_gives_no_suffix(upload_dir, doc):
    file_name = save_student_doc_file(doc, "elstam", make_upload("scan"))
    assert file_name == f"{doc.id}_elstam"
    assert (upload_dir / STUDENT_DOCUMENTS_DIR / file_name).is_file()


def test_reupload_same_extension_overwrites(upload_dir, doc):
    save_student_doc_file(doc, "elstam", make_upload("a.pdf", b"old"))
    file_name = save_student_doc_file(doc, "elstam", make_upload("b.pdf", b"new"))

    stored = upload_dir / STUDENT_DOCUMENTS_DIR / file_name
    assert stored.read_bytes() == b"new"
    assert list((upload_dir / STUDENT_DOCUMENTS_DIR).iterdir()) == [stored]


def test_reupload_different_extension_removes_old_file(upload_dir, doc):
    old_name = save_student_doc_file(doc, "elstam", make_upload("a.pdf"))
    new_name = save_student_doc_file(doc, "elstam", make_upload("a.png"))

    subdir = upload_dir / STUDENT_DOCUMENTS_DIR
    assert not (subdir / old_name).exists()
    assert list(subdir.iterdir()) == [subdir / new_name]


def test_reupload_does_not_touch_other_fields(upload_dir, doc):
    other = save_student_doc_file(doc, "elstam_extra", make_upload("a.pdf"))
    save_student_doc_file(doc, "elstam", make_upload("a.pdf"))
    save_student_doc_file(doc, "elstam", make_upload("a.png"))

    assert (upload_dir / STUDENT_DOCUMENTS_DIR / other).is_file()


@pytest.mark.parametrize(
    "client_name", ["../../x.pdf", "/etc/passwd.pdf", "..\\..\\x.pdf", "a/../../b.pdf"]
)
def test_client_file_name_does_not_influence_path(upload_dir, doc, client_name):
    file_name = save_student_doc_file(doc, "elstam", make_upload(client_name))

    assert file_name == f"{doc.id}_elstam.pdf"
    stored = [p for p in upload_dir.rglob("*") if p.is_file()]
    assert stored == [upload_dir / STUDENT_DOCUMENTS_DIR / file_name]


def test_save_prev_emp_file(upload_dir):
    prev_emp = SimpleNamespace(id=uuid.uuid4())
    file_name = save_prev_emp_file(prev_emp, make_upload("Proof.PDF"))

    assert file_name == f"{prev_emp.id}_proof.pdf"
    assert (upload_dir / PREV_EMPLOYMENTS_DIR / file_name).is_file()


def test_delete_file(upload_dir, doc):
    file_name = save_student_doc_file(doc, "elstam", make_upload("a.pdf"))
    delete_file(STUDENT_DOCUMENTS_DIR, file_name)
    assert not (upload_dir / STUDENT_DOCUMENTS_DIR / file_name).exists()


def test_prev_employment_handler_upload_file(upload_dir):
    from api.handlers.prev_employment_handler import PrevEmploymentHandler

    prev_emp = SimpleNamespace(id=uuid.uuid4(), proof=None)

    class StubManager:
        def get(self, id):
            assert id == prev_emp.id
            return prev_emp

        def update(self, objs, data):
            for obj in objs:
                for key, value in data.items():
                    setattr(obj, key, value)
            return objs

    handler = PrevEmploymentHandler.__new__(PrevEmploymentHandler)
    handler.manager = StubManager()

    handler.upload_file(prev_emp.id, make_upload("proof.pdf"))
    assert prev_emp.proof == f"{prev_emp.id}_proof.pdf"
    assert (upload_dir / PREV_EMPLOYMENTS_DIR / prev_emp.proof).is_file()

    handler.upload_file(prev_emp.id, make_upload("proof.jpg"))
    assert prev_emp.proof == f"{prev_emp.id}_proof.jpg"
    assert [p.name for p in (upload_dir / PREV_EMPLOYMENTS_DIR).iterdir()] == [
        prev_emp.proof
    ]


def test_prev_employment_download_resolves_in_subdir(upload_dir):
    from api.routers.prev_employment import download_prev_employment_proof

    prev_emp = SimpleNamespace(id=uuid.uuid4(), proof="some_proof.pdf")
    path = download_prev_employment_proof(prev_emp.id, prev_emp, user={})
    assert path == upload_dir / PREV_EMPLOYMENTS_DIR / "some_proof.pdf"
