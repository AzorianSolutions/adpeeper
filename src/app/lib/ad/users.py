from loguru import logger
from pyad import adquery, pyad
from app.config import settings
from app.models.users import UserRecord
from app.models.workers import WorkerRecord


class UsersAPI:
    
    def get_users(self, params: dict = None) -> list:
        defaults: dict = {
            'attributes': ['employeeID', 'distinguishedName', 'samAccountName', 'displayName'],
            'base_dn': 'OU=Managed Users,OU=Managed Resources,DC=root,DC=local',
            'search_scope': 'subtree',
        }
        params = {**defaults} if params is None else {**defaults, **params}
        q = adquery.ADQuery()

        q.execute_query(
            attributes=params['attributes'],
            base_dn=params['base_dn'],
            search_scope=params['search_scope']
        )

        users = q.get_results()

        logger.info(f'Total AD Users Retrieved: {len(users)}')

        return users

    def build_users(self) -> list[UserRecord]:
        records: list[UserRecord] = []
        params: dict = {
            'attributes': ['employeeID', 'distinguishedName', 'samAccountName', 'displayName'],
        }
        users: list = self.get_users(params=params)

        for user in users:
            logger.trace(user)

            record: UserRecord = UserRecord()
            record.employee_id = user['employeeID']
            record.distinguished_name = user['distinguishedName']
            record.sam_account_name = user['samAccountName']
            record.display_name = user['displayName']

            records.append(record)

            logger.trace(f'Retrieved user record: {record.dict()}')

        return records

    @staticmethod
    def sync_from_workers(records: list[WorkerRecord] = None):
        # TODO
        logger.success(f'Finished synchronizing ADP workers to Active Directory users.')
