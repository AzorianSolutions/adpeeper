from pydantic import BaseModel


class WorkerRecord(BaseModel):
    """ The worker record represents a single employee export record. """
    id: str = ''
    given_name: str = ''
    middle_name: str = ''
    family_name: str = ''
    phone_number: str = ''
    legal_name: str = ''
    display_name: str = ''
    hire_date: str = ''
    termination_date: str = ''
    status_effective_date: str = ''
    supervisor_id: str = ''
    job_title: str = ''
    division: str = ''
    department: str = ''
    location: str = ''

    @property
    def full_name(self) -> str:
        """ Return the full name of the worker. """
        return f'{self.given_name} {self.family_name}'

    @property
    def formatted_name(self) -> str:
        """ Return the formatted name of the worker. """
        return f'{self.family_name}, {self.given_name} {self.middle_name}'

    def row(self) -> tuple:
        return (
            self.id,
            self.given_name,
            self.middle_name,
            self.family_name,
            self.phone_number,
            self.hire_date,
            self.termination_date,
            self.status_effective_date,
            self.supervisor_id,
            self.job_title,
            self.division,
            self.department,
            self.location,
        )

    @staticmethod
    def records_to_rows(records: list['WorkerRecord']) -> list[tuple]:
        """ Convert a list of worker records to a list of rows. """
        rows: list[tuple] = []
        for record in records:
            rows.append(record.row())
        return rows


class WorkersExportResponse(BaseModel):
    """ The workers data export model. """
    error: str | None
    messages: list[str] | None
    payload: list[WorkerRecord] | None
    status: int = 1

