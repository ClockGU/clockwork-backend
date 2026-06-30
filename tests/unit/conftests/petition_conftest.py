import pytest


@pytest.fixture
def base_petition():
    return {
        "org_unit": "Finance",
        "eos_number": "F123456",
        "start_date": date(2025, 1, 1),
        "end_date": date(2026, 1, 2),  # 366 days — clears the duration exception requirement
        "minutes": 2400,               # exactly 40h — clears the time exception requirement
        "ba_degree": False,
        "student_username": "teststudent",
    }


@pytest.fixture
def budget_position():
    return {
        "budget_position": "SHK",
        "budget_approver": "approver@uni-frankfurt.de",
    }