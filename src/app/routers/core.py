from fastapi import APIRouter

router = APIRouter(
    prefix="/app",
    tags=['app'],
    responses={404: {"description": "Not found"}},
)


@router.get('/status')
async def root():
    return {"message": "ONLINE"}
