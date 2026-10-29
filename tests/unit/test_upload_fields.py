from api.pydantic_models.documents import UPLOAD_FIELDS


def test_upload_fields_lists_all_student_document_files():
    assert UPLOAD_FIELDS == [
        "elstam",
        "studienbescheinigung",
        "versicherungsbescheinigung",
        "sozialversicherungsbogen",
        "ba_degree",
        "residence_permit",
        "id_photo",
    ]
