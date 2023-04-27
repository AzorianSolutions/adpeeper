from fastapi import APIRouter
from app.routers.v1 import base as v1_base

router = APIRouter(
    prefix="/api",
    responses={404: {"description": "Not found"}},
)

# Setup descendent routers
router.include_router(v1_base.router)
