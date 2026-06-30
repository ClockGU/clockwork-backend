import pytest
from pydantic import ValidationError

from api.pydantic_models.budget_position import BudgetPositionCreate
from api.pydantic_models.petition_create import PetitionCreate


class TestValidateBudgetPercentageSum:
    def test_single_position_at_100_passes(self, base_petition, budget_position):
        PetitionCreate(
            **base_petition,
            budget_positions=[BudgetPositionCreate(**budget_position, percentage=100.0)],
        )

    def test_two_positions_summing_to_100_passes(self, base_petition, budget_position):
        PetitionCreate(
            **base_petition,
            budget_positions=[
                BudgetPositionCreate(**budget_position, percentage=60.0),
                BudgetPositionCreate(**budget_position, percentage=40.0),
            ],
        )

    def test_positions_summing_below_100_fails(self, base_petition, budget_position):
        with pytest.raises(ValidationError):
            PetitionCreate(
                **base_petition,
                budget_positions=[
                    BudgetPositionCreate(**budget_position, percentage=60.0),
                    BudgetPositionCreate(**budget_position, percentage=30.0),
                ],
            )

    def test_positions_summing_above_100_fails(self, base_petition, budget_position):
        with pytest.raises(ValidationError):
            PetitionCreate(
                **base_petition,
                budget_positions=[
                    BudgetPositionCreate(**budget_position, percentage=60.0),
                    BudgetPositionCreate(**budget_position, percentage=50.0),
                ],
            )

    def test_floating_point_within_tolerance_passes(self, base_petition, budget_position):
        PetitionCreate(
            **base_petition,
            budget_positions=[
                BudgetPositionCreate(**budget_position, percentage=33.33),
                BudgetPositionCreate(**budget_position, percentage=33.33),
                BudgetPositionCreate(**budget_position, percentage=33.34),
            ],
        )