import sys
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from loguru import logger
from pyad import pyad
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

"""
Setup Active Directory authentication if any overrides provided
"""
pyad_defaults: dict = {}

if isinstance(settings.ad_password, str) and len(settings.ad_password) > 0:
    pyad_defaults['password'] = settings.ad_password

if isinstance(settings.ad_server, str) and len(settings.ad_server) > 0:
    pyad_defaults['ldap_server'] = settings.ad_server

if isinstance(settings.ad_username, str) and len(settings.ad_username) > 0:
    pyad_defaults['username'] = settings.ad_username

if len(pyad_defaults.keys()):
    pyad.set_defaults(**pyad_defaults)

# Automatic Export Scheduling
@app.on_event('startup')
@repeat_every(seconds=settings.export_interval if isinstance(settings.export_interval, int) else 0)
def sync_users_task() -> None:
    """
    Export timer event handler
    :return: None
    """
    SyncTasks.sync_users_to_workers()
