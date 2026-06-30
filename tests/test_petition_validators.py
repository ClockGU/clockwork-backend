from datetime import date

import pytest
from pydantic import ValidationError

from api.pydantic_models.budget_position import BudgetPositionCreate
from api.pydantic_models.petition_create import PetitionCreate

BASE_PETITION = {
    "org_unit": "Finance",
    "eos_number": "F123456",
    "start_date": date(2025, 1, 1),
    "end_date": date(2026, 1, 2),  # 366 days — clears the duration exception requirement
    "minutes": 2400,               # exactly 40h — clears the time exception requirement
    "ba_degree": False,
    "student_username": "teststudent",
}

BUDGET_POSITION = {
    "budget_position": "SHK",
    "budget_approver": "approver@uni-frankfurt.de",

}


class TestValidateBudgetPercentageSum:
    def test_single_position_at_100_passes(self):
        PetitionCreate(
            **BASE_PETITION,
            budget_positions=[BudgetPositionCreate(**BUDGET_POSITION, percentage=100.0)],
        )

    def test_two_positions_summing_to_100_passes(self):
        PetitionCreate(
            **BASE_PETITION,
            budget_positions=[
                BudgetPositionCreate(**BUDGET_POSITION, percentage=60.0),
                BudgetPositionCreate(**BUDGET_POSITION, percentage=40.0)
            ],
        )

    def test_positions_summing_below_100_fails(self):
        with pytest.raises(ValidationError):
            PetitionCreate(
                **BASE_PETITION,
                budget_positions=[
                    BudgetPositionCreate(**BUDGET_POSITION, percentage=60.0),
                    BudgetPositionCreate(**BUDGET_POSITION, percentage=30.0)
                ],
            )

    def test_positions_summing_above_100_fails(self):
        with pytest.raises(ValidationError):
            PetitionCreate(
                **BASE_PETITION,
                budget_positions=[
                    BudgetPositionCreate(**BUDGET_POSITION, percentage=60.0),
                    BudgetPositionCreate(**BUDGET_POSITION, percentage=50.0)
                ],
            )

    def test_floating_point_within_tolerance_passes(self):
        PetitionCreate(
            **BASE_PETITION,
            budget_positions=[
                BudgetPositionCreate(**BUDGET_POSITION, percentage=33.33),
                BudgetPositionCreate(**BUDGET_POSITION, percentage=33.33),
                BudgetPositionCreate(**BUDGET_POSITION, percentage=33.34)
            ],
        )