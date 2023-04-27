import requests
from loguru import logger
from app.lib.adp.api.exceptions import APIConnectionError, APIDisconnectionError, APIRequestDone, APIRequestError
from app.lib.adp.api.static import ApiConnectionStatic
from app.models.adp import ApiConfig, ApiConnection


class BaseAPI:
    _config: ApiConfig
    _connection: ApiConnection
    _connections: dict[str, ApiConnection] = {}
    _session_id: str | None = None

    def __init__(self, config: ApiConfig, auto_connect: bool = True):
        self._config = config
        self._connection = ApiConnection(status=ApiConnectionStatic.STATUS_READY)

        if not isinstance(BaseAPI._connections, dict):
            BaseAPI._connections = {}

        if auto_connect:
            self.connect()

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.config}>'

    def __str__(self):
        return f'{self.config}'

    def __eq__(self, other):
        if isinstance(other, BaseAPI):
            return self.config == other.config
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.config)

    def __bool__(self):
        return bool(len(self.config.__dict__.keys()))

    @property
    def config(self) -> ApiConfig:
        return self._config

    @config.setter
    def config(self, value: ApiConfig):
        self._config = value

    @property
    def connection(self) -> ApiConnection:
        return self._connection

    @connection.setter
    def connection(self, value: ApiConnection):
        self._connection = value

    @property
    def connections(self) -> dict:
        return self._connections

    @connections.setter
    def connections(self, value: dict):
        self._connections = value

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @session_id.setter
    def session_id(self, value: str | None):
        self._session_id = value

    def connect(self, config: ApiConfig = None, cache: bool = True) -> ApiConnection:
        import uuid

        if not isinstance(config, ApiConfig):
            config = self.config

        logger.debug(f'Connecting to ADP token server: {config.token_server_url}')

        request_data = {'grant_type': config.grant_type}
        headers = {'User-Agent': config.user_agent}

        r = requests.post(config.token_server_url,
                          headers=headers,
                          cert=(config.ssl_cert_path,
                                config.ssl_key_path),
                          auth=(config.client_id,
                                config.client_secret),
                          data=request_data)

        if r.status_code != requests.codes.ok:
            raise APIConnectionError(self.__class__.__name__, str(r.status_code), 'Unable to connect to ADP API.')

        response_data = r.json()

        logger.debug(f'Connected to ADP token server ({r.status_code})')
        logger.debug(response_data)

        self._connection = BaseAPI.create_connection(ApiConnectionStatic.STATUS_CONNECTED, response_data['access_token'],
                                                     response_data['expires_in'])

        # Generate a new session ID if one does not exist
        if self.session_id is None or isinstance(self.session_id, str) is False or not len(self.session_id):
            self.session_id = str(uuid.uuid1())

        # Cache the connection by session ID in a class variable
        if cache:
            BaseAPI._connections[self.session_id] = self._connection

        return self.connection

    def disconnect(self):
        logger.debug(f'Disconnecting from ADP API: {self.config.disconnect_url}')

        headers = {'User-Agent': self.config.user_agent}

        r = requests.get(self.config.disconnect_url + '?id_token_hint=' + self.connection.token, headers=headers)

        if r.status_code != requests.codes.ok:
            raise APIDisconnectionError(self.__class__.__name__, str(r.status_code), 'Unable to perform remote '
                                                                                     'disconnect with ADP API.')

        logger.debug(f'Completed ADP remote disconnect: {r}')

        del BaseAPI._connections[self.session_id]
        self._connection.status = ApiConnectionStatic.STATUS_DISCONNECTED
        self._connection.token = None
        self._connection.expires = None
        self.session_id = None

    def get(self, path: str, params: dict = None):
        request_url: str = self.config.api_request_url + path
        headers = {
            'Authorization': f'Bearer {self._connection.token}',
            'User-Agent': self.config.user_agent
        }
        request_args = {
            'headers': headers,
            'cert': (self.config.ssl_cert_path, self.config.ssl_key_path),
        }

        if isinstance(params, dict) and len(params):
            request_args['params'] = params

        logger.debug(f'Making ADP API Request: {request_url}')
        logger.debug(request_args)

        r = requests.get(request_url, **request_args)

        response: dict = r.json() if r.status_code == requests.codes.ok and len(r.content) else {}

        if r.status_code == 204:
            logger.debug(f'Reached the end of the record cursor.')
            raise APIRequestDone(self.__class__.__name__, str(r.status_code), 'Reached the end of the record cursor.',
                                 response)

        if r.status_code != requests.codes.ok:
            logger.error(f'ADP API Request Error: {r.status_code}')
            logger.error(response)
            raise APIRequestError(self.__class__.__name__, str(r.status_code), 'Unable to complete ADP API request.',
                                  response)

        return response

    @staticmethod
    def create_connection(status: str, token: str, expires: int) -> ApiConnection:
        connection = ApiConnection(status=status, token=token)
        connection.expire_in(expires)
        return connection
