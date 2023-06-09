import sys
from loguru import logger
from pyad import pyad
from app.config import settings
from app.lib.tasks.sync import SyncTasks


dry_run: bool = '-d' in sys.argv

"""
Setup logging
"""
logger_params: dict = {
    'colorize': True,
    'format': '<green>{time}</green> <level>{level} {message}</level>',
    'level': 'TRACE' if settings.debug else 'INFO',
}
logger.remove()
logger.add(sys.stderr, **logger_params)

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

if dry_run:
    logger.warning('Dry-run execution mode enabled. No changes will be made to Active Directory users.')

SyncTasks.sync_users_to_workers(dry_run=dry_run)
