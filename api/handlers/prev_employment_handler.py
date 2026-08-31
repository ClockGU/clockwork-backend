from typing import Optional, Self

from sqlmodel import Session

from api.db.managers.prev_employment_manager import PrevEmploymentManager
from api.db.schema.prev_employment import PrevEmployment
from api.handlers.exception_handler import ExceptionHandler
from api.pydantic_models.prev_employment import PrevEmploymentCreate


class PrevEmploymentHandler:

    def __init__(
        self,
        db: Session,
        object_instances: Optional[list[PrevEmployment]] = None,
        prev_employment: Optional[PrevEmployment] = None,
    ):
        self.manager = PrevEmploymentManager(db)
        self.db = db
        self.exc = ExceptionHandler()
        self._object_instances = object_instances
        self._prev_employment = prev_employment

    def get_objects(self):
        if not self._object_instances:
            raise RuntimeError(
                "Calling get_object() is not allowed when no existing objects was provided at initialization."
            )
        return self._object_instances

    def get_prev_employment(self):
        if not self._prev_employment:
            raise RuntimeError(
                "Calling get_petition() is not allowed when no existing petition was provided at initialization."
            )
        return self._prev_employment

    @classmethod
    def from_existing_object(cls, db: Session, object_instance: PrevEmployment) -> Self:
        """
        Explicitly create a PetitionHandler instance from an existing Petition object.
        """
        return cls(db, prev_employment=object_instance)

    def create_prev_employment(self, data, user_id):
        data["user_account"] = user_id
        validated_data = PrevEmploymentCreate.model_validate(data).model_dump()
        return self.manager.create(**validated_data)

    def get_user_prev_employments(self, user_id: str) -> list[PrevEmployment]:
        return self.manager.filter(user_account=user_id)
