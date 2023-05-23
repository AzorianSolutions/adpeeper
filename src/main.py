import sys
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from loguru import logger
from app.config import settings
from app.lib.tasks.sync import SyncTasks
from app.middleware import cors
from app.routers import api, core

"""
Setup logging
"""
if settings.debug:
    logger.add(sys.stderr, colorize=True, format="<green>{time}</green> <level>{message}</level>", level="TRACE")

"""
Instantiate the app instance
"""
app = FastAPI()

"""
Attach middleware to the app instance
"""
# CORS Protection Middleware
cors.setup(app)

"""
Attach routers to the app instance
"""
# Core Router
app.include_router(core.router)
# API Router
app.include_router(api.router)


# Automatic Export Scheduling
@app.on_event('startup')
@repeat_every(seconds=settings.export_interval if isinstance(settings.export_interval, int) else 0)
def sync_users_task() -> None:
    """
    Export timer event handler
    :return: None
    """
    SyncTasks.sync_users_to_workers()
