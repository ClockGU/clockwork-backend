import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from api.consts import PetitionStatus


@pytest.fixture
def base_petition():
    return {
        "org_unit": "Finance",
        "eos_number": "F123456",
        "start_date": date(2025, 1, 1),
        "end_date": date(
            2026, 1, 2
        ),  # 366 days — clears the duration exception requirement
        "minutes": 2400,  # exactly 40h — clears the time exception requirement
        "ba_degree": False,
        "student_username": "teststudent",
    }


@pytest.fixture
def budget_position():
    return {
        "budget_position": "SHK",
        "budget_approver": "approver@uni-frankfurt.de",
        "budget_position_approved": False,
    }


@pytest.fixture
def orm_petition(base_petition):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_account=uuid.uuid4(),
        status=PetitionStatus.APPROVER_ACTION,
        supervisor_mail=None,
        budget_positions=[],
        time_exce_student=None,
        time_exce_course=None,
        time_exce_name=None,
        time_exce_start=None,
        time_exce_end=None,
        time_exce_time=None,
        duration_exce_course=None,
        duration_exce_name=None,
        duration_exce_start=None,
        duration_exce_end=None,
        **base_petition,
    )
