from typing import Optional, Self
from uuid import UUID

from sqlmodel import Session

from api.db.managers.budget_position_manager import BudgetPositionManager
from api.db.schema import BudgetPosition, Petition
from api.handlers import EmailHandler
from api.handlers.exception_handler import ExceptionHandler
from tests.unit.conftests import budget_position


class BudgetPositionsHandler:

    def __init__(
        self,
        db: Session,
        object_instances: Optional[list[BudgetPosition]] = None,
        petition: Optional[Petition] = None,
    ):
        self.manager = BudgetPositionManager(db)
        self.db = db
        self.exc = ExceptionHandler()
        self._object_instances = object_instances
        self._petition = petition

    def get_objects(self):
        if not self._object_instances:
            raise RuntimeError(
                "Calling get_object() is not allowed when no existing objects was provided at initialization."
            )
        return self._object_instances

    def get_petition(self):
        if not self._petition:
            raise RuntimeError(
                "Calling get_petition() is not allowed when no existing petition was provided at initialization."
            )
        return self._petition

    @classmethod
    def from_existing_object(
        cls, db: Session, object_instances: list[BudgetPosition]
    ) -> Self:
        """
        Explicitly create a PetitionHandler instance from an existing Petition object.
        """
        return cls(db, object_instances)

    @classmethod
    def from_petition(cls, db: Session, petition: Petition) -> Self:
        """
        Explicitly create a PetitionHandler instance from an existing Petition object.
        """
        self = cls(db, petition=petition)
        budget_positions = self.manager.get_budget_positions_by_petition(petition)
        self.__set_object_instances(budget_positions)
        return self

    def __set_object_instances(self, value: list[BudgetPosition]):
        self._object_instances = value

    def reset_approval_status(self):
        """
        Reset the approval status of all budget positions associated with the petition to False.
        Send email notifications to budget positions about the status update.
        """
        budget_positions = self.get_objects()
        for budget_position in budget_positions:
            self.manager.update_budget_position_status(budget_position, False)
        try:
            email_handler = EmailHandler(self.get_petition())
            email_handler.send_budget_position_update_emails(budget_positions)
        except Exception as e:
            raise self.exc.internal_error("sending budget position update emails", e)

    def get_assigned_budget_position_by_id(
        self, budget_position_id: UUID
    ) -> Optional[BudgetPosition]:

        for budget_position in self.get_objects():
            if budget_position.id == budget_position_id:
                return budget_position
        return None

    def update_budget_position_status(
        self, budget_position: BudgetPosition, status: bool
    ) -> BudgetPosition:
        updated = self.manager.update_budget_position_status(budget_position, status)
        if not updated:
            raise self.exc.update_failed(
                "Budget position", message="Failed to update budget position"
            )
        return updated

    def check_all_budget_positions_approved(self, petition_id: Optional[UUID]) -> bool:
        if self.get_objects():
            return all(
                budget_position.approved for budget_position in self.get_objects()
            )
        return self.manager.check_all_budget_positions_approved(petition_id)
