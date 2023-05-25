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
    def sync_users_to_workers(dry_run: bool = False) -> UsersSyncResponse:
        api_config: ApiConfig = ApiConfig.create_from_settings(settings)
        workers_api: HRWorkersAPI = HRWorkersAPI(api_config, auto_connect=False)
        connected: bool = False
        response: UsersSyncResponse = UsersSyncResponse()
        response.status = AdStatic.STATUS_SUCCESS
        workers: list[WorkerRecord] | None = None
        users: list[UserRecord] | None = None

        logger.info('Synchronizing Active Directory users from ADP workers...')

        try:
            logger.debug('Connecting to ADP API...')
            connected = workers_api.connect().status == ApiConnectionStatic.STATUS_CONNECTED
        except APIConnectionError as e:
            response.error = str(e)
            response.status = AdStatic.STATUS_ERROR
            logger.error(f'Error connecting to ADP API: {e}')

        if connected:
            try:
                logger.info('Loading ADP workers...')
                workers = workers_api.build_workers()
                logger.debug('ADP workers have been loaded.')
            except APIRequestError as e:
                response.error = str(e)
                response.status = AdStatic.STATUS_ERROR
                logger.error(f'Error requesting workers from ADP API: {e}')

        if not isinstance(workers, list) or not len(workers) or not connected \
                or response.status != AdStatic.STATUS_SUCCESS:
            logger.warning('No ADP worker records were retrieved so there is nothing to sync.')
        else:
            logger.info('Loading AD users...')
            users = UsersAPI.build_users()
            logger.debug('AD users have been loaded.')

            try:
                logger.info('Syncing AD users to ADP workers...')
                reports = UsersAPI.sync_from_workers(users, workers, dry_run)
                logger.debug('AD users have been synchronized from ADP workers.')

                logger.info('Saving post-synchronization reports...')
                UsersAPI.save_reports(reports)
            except ADSyncError as e:
                response.status = AdStatic.STATUS_ERROR
                response.error = str(e)
                logger.error(f'Error synchronizing Active Directory users from ADP workers: {e}')

        if connected:
            try:
                workers_api.disconnect()
            except APIDisconnectionError as e:
                response.error = str(e)
                response.status = AdStatic.STATUS_ERROR
                logger.error(f'Error disconnecting from ADP API: {e}')

        response.payload = users

        if response.status == AdStatic.STATUS_SUCCESS:
            logger.success('Successfully synchronized Active Directory users from ADP workers.')

        return response
