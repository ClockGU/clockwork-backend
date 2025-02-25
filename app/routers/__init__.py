from fastapi import APIRouter

from .petition import router as petition_router

router = APIRouter()

router.include_router(petition_router)