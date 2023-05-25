from loguru import logger
from app.lib.adp.api.base import BaseAPI
from app.lib.adp.api.exceptions import APIRequestDone
from app.models.workers import WorkerRecord


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

            if 'person' in worker and 'legalName' in worker['person']:
                if 'givenName' in worker['person']['legalName']:
                    record.given_name = worker['person']['legalName']['givenName']
                if 'middleName' in worker['person']['legalName']:
                    record.middle_name = worker['person']['legalName']['middleName']
                if 'familyName1' in worker['person']['legalName']:
                    record.family_name = worker['person']['legalName']['familyName1']

            if 'businessCommunication' in worker and 'mobiles' in worker['businessCommunication'] \
                    and len(worker['businessCommunication']['mobiles']):
                record.phone_number = worker['businessCommunication']['mobiles'][0]['formattedNumber']

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

            if 'reportsTo' in assignment and 'workerID' in assignment['reportsTo'][0] \
                    and 'idValue' in assignment['reportsTo'][0]['workerID']:
                record.supervisor_id = assignment['reportsTo'][0]['workerID']['idValue']

            if 'jobTitle' in assignment:
                record.job_title = assignment['jobTitle']

            if 'homeOrganizationalUnits' in assignment:
                total_units: int = len(assignment['homeOrganizationalUnits'])

                if total_units > 0:
                    record.division = assignment['homeOrganizationalUnits'][0]['nameCode']['shortName']

                if total_units > 1:
                    record.department = assignment['homeOrganizationalUnits'][1]['nameCode']['longName']

            if 'homeWorkLocation' in assignment and 'nameCode' in assignment['homeWorkLocation'] \
                    and 'shortName' in assignment['homeWorkLocation']['nameCode']:
                record.location = assignment['homeWorkLocation']['nameCode']['shortName']

            records.append(record)

            logger.debug(f'Retrieved worker record: {record.dict()}')

        return records
