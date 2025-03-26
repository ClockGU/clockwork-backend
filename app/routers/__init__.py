from fastapi import APIRouter

from .petition_supervisor import router as petition_supervisor_router
from .petition_student import router as petition_student_router

router = APIRouter()

router.include_router(petition_supervisor_router)
router.include_router(petition_student_router)
