from api.pydantic_models.petition_read import PetitionRead


def test_model_validate_without_from_attributes(orm_petition):
    result = PetitionRead.model_validate(orm_petition)
    assert result.student_username == orm_petition.student_username