from fastapi import APIRouter

from api.websockets.routers.web_socket import router as web_socket_router

from .document import router as document_student_router
from .email import router as email_router
from .employee import router as employee_router
from .petition_approver import router as petition_approver_router
from .petition_clerk import router as petition_clerk_router
from .petition_student import router as petition_student_router
from .petition_supervisor import router as petition_supervisor_router

router = APIRouter()

# Petition Management - Organized by user role
router.include_router(
    petition_supervisor_router, tags=["Petitions - Supervisor"], prefix=""
)
router.include_router(petition_student_router, tags=["Petitions - Student"], prefix="")
router.include_router(petition_clerk_router, tags=["Petitions - Clerk"], prefix="")
router.include_router(
    petition_approver_router, tags=["Petitions - Approver"], prefix=""
)

# Employee & Document Management
router.include_router(employee_router, tags=["Employee Management"], prefix="")
router.include_router(document_student_router, tags=["Document Management"], prefix="")

# Communication
router.include_router(email_router, tags=["Email & Notifications"], prefix="")
router.include_router(
    web_socket_router, tags=["WebSocket - Real-time Updates"], prefix=""
)
