from loguru import logger
from app.config import settings
from app.lib.ad.base import AdStatic
from app.lib.ad.exceptions import ADSyncError
from app.lib.ad.users import UsersAPI
from app.lib.adp.api.exceptions import APIConnectionError, APIDisconnectionError, APIRequestError
from app.lib.adp.api.static import ApiConnectionStatic
from app.lib.adp.hr.workers import HRWorkersAPI
from app.models.adp import ApiConfig
from app.models.workers import WorkerRecord
from app.models.users import UsersSyncResponse, UserRecord


class SyncTasks:

    @staticmethod
    def sync_users_to_workers() -> UsersSyncResponse:
        api_config: ApiConfig = ApiConfig.create_from_settings(settings)
        workers_api: HRWorkersAPI = HRWorkersAPI(api_config, auto_connect=False)
        connected: bool = False
        response: UsersSyncResponse = UsersSyncResponse()
        response.status = AdStatic.STATUS_SUCCESS
        workers: list[WorkerRecord] | None = None
        users: list[UserRecord] | None = None

        try:
            connected = workers_api.connect().status == ApiConnectionStatic.STATUS_CONNECTED
        except APIConnectionError as e:
            response.error = str(e)
            response.status = AdStatic.STATUS_ERROR
            logger.error(f'Error connecting to ADP API: {e}')

        if connected:
            try:
                logger.debug('Building ADP workers...')
                workers = workers_api.build_workers()
                logger.debug('ADP workers have been built.')
            except APIRequestError as e:
                response.error = str(e)
                response.status = AdStatic.STATUS_ERROR
                logger.error(f'Error requesting workers from ADP API: {e}')

        if isinstance(workers, list) and connected and response.status == AdStatic.STATUS_SUCCESS:
            logger.debug('Building AD users...')
            users = UsersAPI.build_users()
            logger.debug('AD users have been built.')

            try:
                logger.debug('Syncing AD users to ADP workers...')
                UsersAPI.sync_from_workers(users, workers)
                logger.debug('Synchronized AD users to ADP workers.')
            except ADSyncError as e:
                response.status = AdStatic.STATUS_ERROR
                response.error = str(e)
                logger.error(f'Error synchronizing Active Directory users from ADP workers: {e}')
        else:
            logger.warning('No ADP worker records were retrieved so there is nothing to sync.')

        if connected:
            try:
                workers_api.disconnect()
            except APIDisconnectionError as e:
                response.error = str(e)
                response.status = AdStatic.STATUS_ERROR
                logger.error(f'Error disconnecting from ADP API: {e}')

        response.payload = users

        return response
