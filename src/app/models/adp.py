import datetime

from pydantic import BaseModel
from app.config import AppSettings


class ApiConfig(BaseModel):
    api_request_url: str
    client_id: str
    client_secret: str
    disconnect_url: str
    grant_type: str
    ssl_cert_path: str
    ssl_key_path: str
    token_server_url: str
    user_agent: str

    @staticmethod
    def create_from_settings(settings: AppSettings):
        return ApiConfig(
            api_request_url=settings.adp_api_request_url,
            client_id=settings.adp_client_id,
            client_secret=settings.adp_client_secret,
            disconnect_url=settings.adp_disconnect_url,
            grant_type=settings.adp_grant_type,
            ssl_cert_path=settings.adp_ssl_cert_path,
            ssl_key_path=settings.adp_ssl_key_path,
            token_server_url=settings.adp_token_server_url,
            user_agent=settings.adp_user_agent
        )


class ApiConnection(BaseModel):
    expires: datetime.datetime = None
    status: str = 'ready'
    token: str | None = None

    def expire_in(self, seconds: int):
        self.expires = datetime.datetime.now() + datetime.timedelta(0, seconds, 0)
