from fastapi import APIRouter

from .petition_supervisor import router as petition_supervisor_router
from .petition_student import router as petition_student_router
from .petition_clerk import router as petition_clerk_router
from .document import router as document_student_router
from .employee import router as employee_router
from .email import router as email_router
from .web_socket import router as web_socket_router

router = APIRouter()

router.include_router(petition_supervisor_router)
router.include_router(petition_student_router)
router.include_router(petition_clerk_router)
router.include_router(document_student_router)
router.include_router(employee_router)
router.include_router(email_router)
router.include_router(web_socket_router)
