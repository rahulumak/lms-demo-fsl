from fastapi import APIRouter
from app.api.v1.endpoints import auth, catalog, instructor, student

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(catalog.router)
router.include_router(instructor.router)
router.include_router(student.router)
