from loguru import logger
from pathlib import Path
from app.config import settings
from app.lib.adp.api.base import BaseAPI
from app.lib.adp.api.exceptions import APIRequestDone
from app.models.export import WorkerRecord


class HRWorkersAPI(BaseAPI):
    API_ENDPOINT_PATH = '/hr/v2/workers'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_workers(self, params: dict = None) -> list[dict]:
        if params is None:
            params = {'$top': 1000, '$skip': 0}

        logger.debug(f'Getting workers from ADP with params: {params}')

        workers = self.get(self.API_ENDPOINT_PATH, params=params)['workers']
        last_total: int = len(workers)

        while last_total >= 100:
            params['$skip'] += 100
            logger.debug(f'Getting workers from ADP with params: {params}')
            try:
                workers += self.get(self.API_ENDPOINT_PATH, params=params)['workers']
            except APIRequestDone:
                break
            last_total = len(workers)

        logger.info(f'Total ADP Workers Retrieved: {len(workers)}')

        return workers

    def build_workers(self) -> list[WorkerRecord]:
        records: list[WorkerRecord] = []
        workers: list = self.get_workers(params={'$top': 1000, '$skip': 0})

        for worker in workers:
            logger.trace(worker)

            if 'workerStatus' in worker and 'statusCode' in worker['workerStatus'] \
                    and 'codeValue' in worker['workerStatus']['statusCode'] \
                    and worker['workerStatus']['statusCode']['codeValue'] != 'Active':
                logger.debug(f'Skipping inactive worker {worker["workerID"]["idValue"]}.')
                continue

            if 'workAssignments' not in worker or not len(worker['workAssignments']):
                logger.warning(f'Worker {worker["workerID"]["idValue"]} has no assignments.')
                continue

            assignment: dict = worker['workAssignments'][0]
            record: WorkerRecord = WorkerRecord()

            if 'workerID' in worker and 'idValue' in worker['workerID']:
                record.id = worker['workerID']['idValue']

            if 'person' in worker and 'legalName' in worker['person'] \
                    and 'formattedName' in worker['person']['legalName']:
                record.legal_name = worker['person']['legalName']['formattedName']

            if 'workerDates' in worker:
                if 'originalHireDate' in worker['workerDates']:
                    record.hire_date = worker['workerDates']['originalHireDate']
                if 'terminationDate' in worker['workerDates']:
                    record.termination_date = worker['workerDates']['terminationDate']

            if not len(record.hire_date) and 'actualStartDate' in assignment:
                record.hire_date = assignment['actualStartDate']

            if not len(record.termination_date) and 'terminationDate' in assignment:
                record.termination_date = assignment['terminationDate']

            if 'assignmentStatus' in assignment:
                if 'effectiveDate' in assignment['assignmentStatus']:
                    record.status_effective_date = assignment['assignmentStatus']['effectiveDate']

            if 'jobTitle' in assignment:
                record.job_title = assignment['jobTitle']

            if 'reportsTo' in assignment and 'reportsToWorkerName' in assignment['reportsTo'][0] \
                    and 'formattedName' in assignment['reportsTo'][0]['reportsToWorkerName']:
                record.supervisor_name = assignment['reportsTo'][0]['reportsToWorkerName']['formattedName']

            if 'homeWorkLocation' in assignment and 'address' in assignment['homeWorkLocation'] \
                    and 'cityName' in assignment['homeWorkLocation']['address']:
                record.city_name = assignment['homeWorkLocation']['address']['cityName']

            if 'homeWorkLocation' in assignment and 'address' in assignment['homeWorkLocation'] \
                    and 'countrySubdivisionLevel1' in assignment['homeWorkLocation']['address'] \
                    and 'codeValue' in assignment['homeWorkLocation']['address']['countrySubdivisionLevel1']:
                record.state_code = assignment['homeWorkLocation']['address']['countrySubdivisionLevel1']['codeValue']

            records.append(record)

            logger.trace(f'Retrieved worker record: {record.dict()}')

        return records

    @staticmethod
    def export_workers(records: list[WorkerRecord] = None):
        export_formats: str = ', '.join(settings.export_formats)
        export_path: str = str(Path(settings.export_path) / settings.export_file_name)

        logger.info(f'Exporting {len(records)} employee records in [{export_formats}] format(s).')

        if 'csv' in settings.export_formats:
            import csv

            logger.info(f'Saving employee records CSV to: {export_path}.csv')

            with open(export_path + '.csv', 'w', newline='') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(settings.export_headers)
                writer.writerows(WorkerRecord.records_to_rows(records))
                f.close()

        if 'json' in settings.export_formats:
            import jsonpickle

            logger.info(f'Saving employee records JSON to: {export_path}.json')

            with open(export_path + '.json', 'w') as f:
                f.write(jsonpickle.encode(records))
                f.close()

        logger.success(f'Finished exporting ADP workers to file system.')