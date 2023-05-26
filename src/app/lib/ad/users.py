import os
from loguru import logger
from pyad import adquery, pyad
from app.config import settings
from app.lib.ad.exceptions import ADMapError, ADSyncError
from app.models.users import UserRecord
from app.models.workers import WorkerRecord


class UsersAPI:
    ACTION_TYPE_ALERT: str = 'alert'
    ACTION_TYPE_UPDATE: str = 'update'
    FIELD_TYPE_DICT: str = 'dict'
    FIELD_TYPE_INT: str = 'int'
    FIELD_TYPE_LIST: str = 'list'
    FIELD_TYPE_STR: str = 'str'

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
            'attributes': ['employeeID', 'canonicalName', 'distinguishedName', 'samAccountName', 'displayName',
                           'manager', 'division', 'department', 'title', 'description', 'physicalDeliveryOfficeName',
                           'telephoneNumber', 'mobile'],
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
            record.manager = user['manager']
            record.division = user['division']
            record.department = user['department']
            record.title = user['title']
            record.description = user['description']
            record.office = user['physicalDeliveryOfficeName']
            record.office_phone = user['telephoneNumber']
            record.mobile = user['mobile']

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
            field_map: dict = {
                'employeeID': (UsersAPI.ACTION_TYPE_UPDATE, 'id', UsersAPI.FIELD_TYPE_STR),
                'identity': (UsersAPI.ACTION_TYPE_ALERT, 'sam_account_name', UsersAPI.FIELD_TYPE_STR),
                'displayName': (UsersAPI.ACTION_TYPE_ALERT, 'full_name', UsersAPI.FIELD_TYPE_STR),
                'mobile': (UsersAPI.ACTION_TYPE_UPDATE, 'phone_number', UsersAPI.FIELD_TYPE_LIST),
                'telephoneNumber': (UsersAPI.ACTION_TYPE_UPDATE, 'phone_number', UsersAPI.FIELD_TYPE_LIST),
                'title': (UsersAPI.ACTION_TYPE_UPDATE, 'job_title', UsersAPI.FIELD_TYPE_STR),
                'description': (UsersAPI.ACTION_TYPE_UPDATE, 'job_title', UsersAPI.FIELD_TYPE_LIST),
                'division': (UsersAPI.ACTION_TYPE_UPDATE, 'division', UsersAPI.FIELD_TYPE_STR),
                'department': (UsersAPI.ACTION_TYPE_UPDATE, 'department', UsersAPI.FIELD_TYPE_STR),
                'physicalDeliveryOfficeName': (UsersAPI.ACTION_TYPE_UPDATE, 'location', UsersAPI.FIELD_TYPE_STR),
            }

            for user_property, (action_type, worker_property, field_type) in field_map.items():
                if not hasattr(user, user_property):
                    logger.error(f'User record for worker {worker.id} ({worker.full_name}) does not have '
                                 f'a {user_property} attribute.')
                    continue

                if not hasattr(worker, worker_property):
                    logger.error(f'Worker record for worker {worker.id} ({worker.full_name}) does not have '
                                 f'a {worker_property} attribute.')
                    continue

                log_msg: str = 'Updating' if action_type == UsersAPI.ACTION_TYPE_UPDATE else 'Alerting'
                log_msg += f' {user_property} for worker {worker.id} ({worker.full_name}).'

                different: bool = False
                user_value = getattr(user, user_property)
                user_value_str: str = str(user_value).strip()
                worker_value: str = str(getattr(worker, worker_property)).strip()

                if field_type == UsersAPI.FIELD_TYPE_LIST:
                    final_value: list = list(user_value)
                    if worker_value not in final_value:
                        user_value_str = ', '.join(final_value)
                        different = True
                        if action_type == UsersAPI.ACTION_TYPE_UPDATE:
                            attributes[user_property] = final_value + [worker_value]
                            dirty = True

                elif field_type in (UsersAPI.FIELD_TYPE_STR, UsersAPI.FIELD_TYPE_INT):
                    if user_value != worker_value:
                        different = True
                        if action_type == UsersAPI.ACTION_TYPE_UPDATE:
                            attributes[user_property] = worker_value
                            dirty = True

                if different:
                    logger.debug(log_msg)
                    actions_report.append(
                        (worker.id, worker.full_name, user_property, action_type, user_value_str, worker_value))

            if isinstance(worker.supervisor_id, str) and len(worker.supervisor_id) \
                    and str(worker.supervisor_id).strip() in user_map:
                supervisor: UserRecord = user_map[worker.supervisor_id]
                if str(user.manager).strip() != str(supervisor.dn).strip():
                    logger.debug(f'Updating manager for worker {worker.id} ({worker.full_name}).')
                    attributes['manager'] = supervisor.dn
                    dirty = True
                    actions_report.append(
                        (worker.id, worker.full_name, 'manager', 'UPDATE', user.manager, supervisor.dn))

            if not dry_run and dirty:
                logger.debug(f'Updating AD user attributes for worker {worker.id} ({worker.full_name})...')
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
