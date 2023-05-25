import os
from loguru import logger
from pyad import adquery, pyad
from app.config import settings
from app.lib.ad.exceptions import ADMapError, ADSyncError
from app.models.users import UserRecord
from app.models.workers import WorkerRecord


class UsersAPI:

    @staticmethod
    def get_users(params: dict = None) -> list:
        defaults: dict = {
            'attributes': ['employeeID', 'canonicalName', 'distinguishedName', 'samAccountName', 'displayName'],
            'base_dn': 'OU=Managed Users,OU=Managed Resources,DC=root,DC=local',
            'search_scope': 'subtree',
        }
        params = {**defaults} if params is None else {**defaults, **params}

        logger.debug('Connecting to Active Directory...')

        q = adquery.ADQuery()

        logger.debug('Querying Active Directory....')

        q.execute_query(
            attributes=params['attributes'],
            base_dn=params['base_dn'],
            search_scope=params['search_scope']
        )

        logger.debug('Retrieving query results...')

        users = list(q.get_results())

        logger.info(f'Total AD Users Retrieved: {len(users)}')

        return users

    @staticmethod
    def build_users() -> list[UserRecord]:
        records: list[UserRecord] = []
        params: dict = {
            'attributes': ['employeeID', 'canonicalName', 'distinguishedName', 'samAccountName', 'displayName'],
        }
        users: list = UsersAPI.get_users(params=params)

        for user in users:
            logger.debug(user)

            record: UserRecord = UserRecord()
            record.employee_id = user['employeeID']
            record.cn = user['canonicalName']
            record.dn = user['distinguishedName']
            record.sam_account_name = user['samAccountName']
            record.display_name = user['displayName']

            records.append(record)

            logger.debug(f'Retrieved user record: {record.dict()}')

        return records

    @staticmethod
    def map_users(key: str, users: list[UserRecord]) -> dict[str, UserRecord]:
        user_map: dict[str, UserRecord] = {}

        if not isinstance(users, list):
            raise TypeError('Users argument must be a list of UserRecord objects.')

        if not len(users):
            raise ValueError('Users argument must not be empty.')

        for user in users:
            if not isinstance(user, UserRecord):
                raise TypeError('Users argument must be a list of UserRecord objects.')

            if not hasattr(user, key):
                raise ADMapError(f'UserRecord objects must have a {key} attribute.')

            user_map[getattr(user, key)] = user

        return user_map

    @staticmethod
    def sync_from_workers(users: list[UserRecord], workers: list[WorkerRecord], dry_run: bool = False):
        import csv

        if not isinstance(users, list):
            raise TypeError('users argument must be a list of UserRecord objects.')

        if not len(users):
            raise ValueError('users argument must not be empty.')

        if not isinstance(workers, list):
            raise TypeError('workers argument must be a list of WorkerRecord objects.')

        if not len(workers):
            raise ValueError('workers argument must not be empty.')

        user_map: dict[str, UserRecord] = UsersAPI.map_users('employee_id', users)
        actions_report: list[tuple] = []
        unlinked_report: list[WorkerRecord] = []

        for worker in workers:
            logger.debug(f'Syncing worker {worker.legal_name} to Active Directory...')
            logger.debug(worker)

            user: UserRecord | None

            if worker.id in user_map:
                user = user_map[worker.id]
            else:
                user = UsersAPI.find_user_by_name(users, worker.legal_name)

            if user is None:
                unlinked_report.append(worker)
                logger.error(f'Could not find user record for worker {worker.id} ({worker.legal_name}).')
                continue

            logger.debug(f'Found user record for worker {worker.id} ({worker.legal_name}).')

            dirty: bool = False
            attributes: dict = {}

            if user.employee_id != worker.id:
                logger.debug(f'Updating employeeID for worker {worker.id} ({worker.legal_name}).')
                attributes['employeeID'] = worker.id
                actions_report.append((worker.id, worker.legal_name, 'employeeID', user.employee_id, worker.id))
                dirty = True

            if user.identity != user.sam_account_name:
                logger.debug(f'Updating identity for worker {worker.id} ({worker.legal_name}).')
                attributes['identity'] = user.sam_account_name
                actions_report.append((worker.id, worker.legal_name, 'identity', user.identity, user.sam_account_name))
                dirty = True

            if user.display_name != worker.legal_name:
                logger.debug(f'Updating displayName for worker {worker.id} ({worker.legal_name}).')
                attributes['displayName'] = worker.legal_name
                actions_report.append((worker.id, worker.legal_name, 'displayName', user.display_name,
                                       worker.legal_name))
                dirty = True

            if user.title != worker.job_title:
                logger.debug(f'Updating title for worker {worker.id} ({worker.legal_name}).')
                attributes['title'] = worker.job_title
                actions_report.append((worker.id, worker.legal_name, 'title', user.title, worker.job_title))
                dirty = True

            if user.description != worker.job_title:
                logger.debug(f'Updating description for worker {worker.id} ({worker.legal_name}).')
                attributes['description'] = worker.job_title
                actions_report.append((worker.id, worker.legal_name, 'description', user.description, worker.job_title))
                dirty = True

            if not dry_run and dirty:
                pyad.from_dn(user.dn).update_attributes(attributes)

        logger.success(f'Finished ' + (' dry-run of' if dry_run else '')
                       + 'synchronizing ADP workers to Active Directory users.')

        # Create a CSV report of actions taken
        if len(actions_report):
            if not os.access(settings.report_path_actions, os.W_OK):
                raise ADSyncError(f'Cannot write to actions report file at {settings.report_path_actions}.')

            rows: list[list] = [['workerID', 'legalName', 'attribute', 'oldValue', 'newValue']]

            for action in actions_report:
                rows.append(list(action))

            with open(settings.report_path_actions, 'w') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(rows)
                f.close()

            logger.info(f'Wrote actions report to {settings.report_path_actions}.')

        # Create a CSV report of unlinked workers if there are any
        if len(unlinked_report):
            if not os.access(settings.report_path_unlinked, os.W_OK):
                raise ADSyncError(f'Cannot write to unlinked report file at {settings.report_path_unlinked}.')

            rows: list[list] = [['workerID', 'legalName', 'formattedName', 'jobTitle', 'department', 'location',
                                 'managerID']]

            for worker in unlinked_report:
                rows.append([worker.id, worker.legal_name, worker.formatted_name, worker.job_title, worker.department,
                             worker.location, worker.manager_id])

            with open(settings.report_path_unlinked, 'w') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(rows)
                f.close()

            logger.info(f'Created a report of unlinked workers at {settings.report_path_unlinked}.')
            logger.debug(unlinked_report)

    @staticmethod
    def find_user_by_name(users: list[UserRecord], name: str) -> UserRecord | None:
        for user in users:
            if user.display_name == name:
                return user
        return None
