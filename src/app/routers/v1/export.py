from fastapi import APIRouter
from loguru import logger
from app.lib.tasks.export import ExportTasks
from app.models.workers import WorkersExportResponse, WorkerRecord

router = APIRouter(
    prefix="/export",
    tags=["export"],
    responses={404: {"description": "Not found"}},
)


@router.get('/workers')
async def export_workers() -> WorkersExportResponse:
    logger.info('Exporting workers from ADP')
    return ExportTasks.export_workers()
