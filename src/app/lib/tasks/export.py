from loguru import logger
from app.config import settings
from app.lib.adp.api.exceptions import APIConnectionError, APIDisconnectionError, APIRequestError
from app.lib.adp.api.static import ApiConnectionStatic, ApiStatic
from app.lib.adp.hr.workers import HRWorkersAPI
from app.models.adp import ApiConfig
from app.models.export import WorkersExportResponse, WorkerRecord


class ExportTasks:

    @staticmethod
    def export_workers() -> WorkersExportResponse:
        api_config: ApiConfig = ApiConfig.create_from_settings(settings)
        workers_api: HRWorkersAPI = HRWorkersAPI(api_config, auto_connect=False)
        connected: bool = False
        response: WorkersExportResponse = WorkersExportResponse()
        response.status = ApiStatic.STATUS_SUCCESS
        workers: list[WorkerRecord] | None = None

        try:
            connected = workers_api.connect().status == ApiConnectionStatic.STATUS_CONNECTED
        except APIConnectionError as e:
            response.error = str(e)
            response.status = ApiStatic.STATUS_ERROR
            logger.error(f'Error connecting to ADP API: {e}')

        if connected:
            try:
                workers = workers_api.build_workers()
            except APIRequestError as e:
                response.error = str(e)
                response.status = ApiStatic.STATUS_ERROR
                logger.error(f'Error requesting workers from ADP API: {e}')

        if isinstance(workers, list) and connected and response.status == ApiStatic.STATUS_SUCCESS:
            try:
                workers_api.export_workers(workers)
            except IOError as e:
                response.error = str(e)
                response.status = ApiStatic.STATUS_ERROR
                logger.error(f'Error exporting workers to file: {e}')

        if connected:
            try:
                workers_api.disconnect()
            except APIDisconnectionError as e:
                response.error = str(e)
                response.status = ApiStatic.STATUS_ERROR
                logger.error(f'Error disconnecting from ADP API: {e}')

        if connected and response.status == ApiStatic.STATUS_SUCCESS:
            response.payload = workers

        return response
