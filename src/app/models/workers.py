from pydantic import BaseModel


class WorkerRecord(BaseModel):
    """ The worker record represents a single employee export record. """
    id: str = ''
    legal_name: str = ''
    hire_date: str = ''
    termination_date: str = ''
    status_effective_date: str = ''
    job_title: str = ''
    supervisor_id: str = ''
    city_name: str = ''
    state_code: str = ''
    phone_number: str = ''

    @property
    def location(self) -> str:
        return f'{self.city_name}, {self.state_code}'

    def row(self) -> tuple:
        return (
            self.legal_name,
            self.id,
            self.hire_date,
            self.termination_date,
            self.status_effective_date,
            self.job_title,
            self.supervisor_id,
            self.location,
            self.phone_number,
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

