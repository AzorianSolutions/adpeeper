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

        logger.warning('Connecting to Active Directory...')

        q = adquery.ADQuery()

        logger.warning('Querying Active Directory....')

        q.execute_query(
            attributes=params['attributes'],
            base_dn=params['base_dn'],
            search_scope=params['search_scope']
        )

        logger.warning('Retrieving query results...')

        users = q.get_results()

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
    def sync_from_workers(users: list[UserRecord], workers: list[WorkerRecord]):

        if not isinstance(users, list):
            raise TypeError('users argument must be a list of UserRecord objects.')

        if not len(users):
            raise ValueError('users argument must not be empty.')

        if not isinstance(workers, list):
            raise TypeError('workers argument must be a list of WorkerRecord objects.')

        if not len(workers):
            raise ValueError('workers argument must not be empty.')

        # if True:
        #     raise ADSyncError('Active Directory synchronization could not be completed.')

        user_map: dict[str, UserRecord] = UsersAPI.map_users('employee_id', users)

        print(user_map)

        # TODO

        logger.success(f'Finished synchronizing ADP workers to Active Directory users.')
