import sys
from loguru import logger
from pyad import pyad
from app.config import settings
from app.lib.tasks.sync import SyncTasks

"""
Setup logging
"""
if settings.debug:
    logger.add(sys.stderr, colorize=True, format="<green>{time}</green> <level>{message}</level>", level="TRACE")
else:
    logger.add(sys.stderr, colorize=True, format="<green>{time}</green> <level>{message}</level>", level="INFO")

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

SyncTasks.sync_users_to_workers(dry_run=True)
