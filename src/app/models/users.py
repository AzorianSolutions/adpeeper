from pydantic import BaseModel


class UserRecord(BaseModel):
    """ The user record represents a single Active Directory user. """

    company: str = 'Point Broadband'
    cn: str = ''
    department: str = ''
    description: list[str] = ''
    display_name: str = ''
    division: str = ''
    dn: str = ''
    employee_id: str = ''
    id: str = ''
    identity: str = ''
    manager: str = ''
    mobile: str = ''
    office: str = ''
    office_phone: str = ''
    sam_account_name: str = ''
    title: str = ''

    def row(self) -> tuple:
        return (
            self.company,
            self.cn,
            self.department,
            "\n".join(self.description),
            self.display_name,
            self.division,
            self.dn,
            self.employee_id,
            self.id,
            self.identity,
            self.manager,
            self.mobile,
            self.office,
            self.office_phone,
            self.sam_account_name,
            self.title,
        )

    @staticmethod
    def records_to_rows(records: list['UserRecord']) -> list[tuple]:
        """ Convert a list of user records to a list of rows. """
        rows: list[tuple] = []
        for record in records:
            rows.append(record.row())
        return rows


class UsersSyncResponse(BaseModel):
    """ The users data sync model. """
    error: str | None
    messages: list[str] | None
    payload: list[UserRecord] | None
    status: int = 1

