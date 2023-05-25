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
    def sync_from_workers(users: list[UserRecord], workers: list[WorkerRecord], dry_run: bool = False) \
            -> tuple[list[tuple], list[WorkerRecord]]:
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
            logger.debug(f'Syncing worker {worker.full_name} to Active Directory...')
            logger.debug(worker)

            user: UserRecord | None

            if worker.id in user_map:
                user = user_map[worker.id]
            else:
                user = UsersAPI.find_user_by_name(users, worker.full_name)

            if user is None:
                unlinked_report.append(worker)
                logger.error(f'Could not find user record for worker {worker.id} ({worker.full_name}).')
                continue

            logger.debug(f'Found user record for worker {worker.id} ({worker.full_name}).')

            dirty: bool = False
            attributes: dict = {}

            if user.employee_id != worker.id:
                logger.debug(f'Updating employeeID for worker {worker.id} ({worker.full_name}).')
                attributes['employeeID'] = worker.id
                actions_report.append(
                    (worker.id, worker.full_name, 'employeeID', 'UPDATE', user.employee_id, worker.id))
                dirty = True

            if user.identity != user.sam_account_name:
                logger.debug(f'Updating identity for worker {worker.id} ({worker.full_name}).')
                # attributes['identity'] = user.sam_account_name
                actions_report.append(
                    (worker.id, worker.full_name, 'identity', 'ALERT', user.identity, user.sam_account_name))
                dirty = True

            if user.display_name != worker.full_name:
                logger.debug(f'Difference in displayName for worker {worker.id} ({worker.full_name}).')
                # attributes['displayName'] = worker.full_name
                actions_report.append((worker.id, worker.full_name, 'displayName', 'ALERT', user.display_name,
                                       worker.full_name))
                dirty = True

            if user.mobile != worker.phone_number:
                logger.debug(f'Updating mobile for worker {worker.id} ({worker.full_name}).')
                attributes['mobile'] = worker.phone_number
                actions_report.append((worker.id, worker.full_name, 'mobile', 'UPDATE', user.mobile,
                                       worker.phone_number))
                dirty = True

            if user.office_phone != worker.phone_number:
                logger.debug(f'Updating officePhone for worker {worker.id} ({worker.full_name}).')
                attributes['officePhone'] = worker.phone_number
                actions_report.append((worker.id, worker.full_name, 'officePhone', 'UPDATE', user.office_phone,
                                       worker.phone_number))
                dirty = True

            if user.title != worker.job_title:
                logger.debug(f'Updating title for worker {worker.id} ({worker.full_name}).')
                attributes['title'] = worker.job_title
                actions_report.append((worker.id, worker.full_name, 'title', 'UPDATE', user.title, worker.job_title))
                dirty = True

            if user.description != worker.job_title:
                logger.debug(f'Updating description for worker {worker.id} ({worker.full_name}).')
                attributes['description'] = worker.job_title
                actions_report.append(
                    (worker.id, worker.full_name, 'description', 'UPDATE', user.description, worker.job_title))
                dirty = True

            if user.division != worker.division:
                logger.debug(f'Updating division for worker {worker.id} ({worker.full_name}).')
                attributes['division'] = worker.division
                actions_report.append(
                    (worker.id, worker.full_name, 'division', 'UPDATE', user.division, worker.division))
                dirty = True

            if user.department != worker.department:
                logger.debug(f'Updating department for worker {worker.id} ({worker.full_name}).')
                attributes['department'] = worker.department
                actions_report.append(
                    (worker.id, worker.full_name, 'department', 'UPDATE', user.department, worker.department))
                dirty = True

            if user.office != worker.location:
                logger.debug(f'Updating office for worker {worker.id} ({worker.full_name}).')
                attributes['office'] = worker.location
                actions_report.append((worker.id, worker.full_name, 'office', 'UPDATE', user.office, worker.location))
                dirty = True

            if isinstance(worker.supervisor_id, str) and len(worker.supervisor_id) \
                    and worker.supervisor_id in user_map:
                supervisor: UserRecord = user_map[worker.supervisor_id]
                if user.manager != supervisor.dn:
                    logger.debug(f'Updating manager for worker {worker.id} ({worker.full_name}).')
                    attributes['manager'] = supervisor.dn
                    actions_report.append(
                        (worker.id, worker.full_name, 'manager', 'UPDATE', user.manager, supervisor.dn))
                    dirty = True

            if not dry_run and dirty:
                pyad.from_dn(user.dn).update_attributes(attributes)

        return actions_report, unlinked_report

    @staticmethod
    def save_reports(actions_report: list[tuple], unlinked_report: list[WorkerRecord]):
        import csv

        # Create a CSV report of actions taken
        if not len(actions_report):
            logger.info('No actions to report.')
        else:
            rows: list[list] = [['workerID', 'fullName', 'attribute', 'action', 'oldValue', 'newValue']]

            for action in actions_report:
                rows.append(list(action))

            with open(settings.report_path_actions, 'w') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(rows)
                f.close()

            logger.info(f'Wrote actions report to {settings.report_path_actions}.')

        # Create a CSV report of unlinked workers if there are any
        if not len(unlinked_report):
            logger.info('No unlinked workers to report.')
        else:
            rows: list[list] = [['workerID', 'fullName', 'jobTitle', 'division', 'department', 'location',
                                 'managerID', 'managerName']]

            for worker in unlinked_report:
                rows.append([worker.id, worker.full_name, worker.job_title, worker.division, worker.department,
                             worker.location, worker.supervisor_id, worker.supervisor_name])

            with open(settings.report_path_unlinked, 'w') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(rows)
                f.close()

            logger.info(f'Wrote unlinked workers report to {settings.report_path_unlinked}.')

    @staticmethod
    def find_user_by_name(users: list[UserRecord], name: str) -> UserRecord | None:
        for user in users:
            if user.display_name == name:
                return user
        return None
