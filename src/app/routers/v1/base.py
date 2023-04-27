from fastapi import APIRouter
from app.routers.v1 import export

router = APIRouter(
    prefix="/v1",
    responses={404: {"description": "Not found"}},
)

# Setup descendent routers
router.include_router(export.router)
