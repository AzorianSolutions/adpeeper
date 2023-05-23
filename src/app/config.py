import os
import yaml
from pathlib import Path
from pydantic import BaseSettings

ROOT_PATH: Path = Path(__file__).parent.parent.parent
""" The root path of the application which is typically the project repository root path. """

SRC_PATH: Path = ROOT_PATH / 'src'
""" The source path of the application which is typically the src directory within the ROOT_PATH. """

DEFAULT_ENV_PATH: Path = Path('/etc/adpeeper/adpeeper.env')
""" The default path to the environment file to load settings from. """

DEFAULT_SECRETS_PATH: Path | None = None
""" The default path to the secrets directory to load environment variable values from. """


class AppSettings(BaseSettings):
    """ The application settings class that loads setting values from the application environment. """

    ad_password: str = ''
    ad_server: str = ''
    ad_username: str = ''
    adp_accounts_api_url: str = 'https://accounts.adp.com'
    adp_api_request_url: str = 'https://api.adp.com'
    adp_disconnect_url: str = 'https://accounts.adp.com/auth/oauth/v2/logout'
    adp_client_id: str | None = None
    adp_client_secret: str | None = None
    adp_grant_type: str = 'client_credentials'
    adp_ssl_cert_path: str | None = None
    adp_ssl_key_path: str | None = None
    adp_token_server_url: str = 'https://api.adp.com/auth/oauth/v2/token'
    adp_user_agent: str = 'ADPeeper/0.1.0'
    config_path: str = '/etc/adpeeper/config.yml'
    cors_allow_credentials: bool = True
    cors_headers: list[str] = ['*']
    cors_methods: list[str] = ['*']
    cors_origins: list[str] = ['http://127.0.0.1', 'http://127.0.0.1:8080', 'http://localhost', 'http://localhost:8080']
    debug: bool = False
    export_file_name: str = 'adp-workers-export'
    export_formats: list[str] = ['csv', 'json']  # csv, json
    export_headers: tuple | str = ('Payroll Name', 'Associate ID', 'Hire Date', 'Termination Date',
                                   'Status Effective Date', 'Job Title Description', 'Reports To Legal Name',
                                   'Location Description', 'Work Contact: Work Phone')
    export_interval: int = 1440  # 24 hours
    export_path: str = '/var/tmp/adpeeper'
    proxy_root: str = '/'
    root_path: str = str(ROOT_PATH)
    salt: str | None = None
    secret_key: str = 'INSECURE-CHANGE-ME-6up8zksTD6mi4N3z3zFk'
    server_address: str = '0.0.0.0'
    server_port: int = 8080
    server_type: str | None = 'uvicorn'  # gunicorn, uvicorn, uwsgi

    version: str = '0.1.0'
    """ The application version number """

    """ The following settings are automatically loaded at application startup. """

    config: dict | None = None
    """ Additional configuration settings loaded automatically from the given YAML configuration file (if any) """

    class Config:
        env_prefix = 'adp_'
        env_nested_delimiter = '__'


def load_settings(env_file_path: str | None = None, env_file_encoding: str | None = None,
                  secrets_path: str | None = None) -> AppSettings:
    """ Loads an AppSettings instance based on the given environment file and secrets directory. """

    # Extract the default environment file path from the environment if defined, otherwise use the default path
    if env_file_path is None:
        env_file_path = os.getenv('ADP_ENV_FILE', DEFAULT_ENV_PATH)

    # Extract the default environment file encoding from the environment if defined, otherwise use the default value
    if env_file_encoding is None:
        env_file_encoding = os.getenv('ADP_ENV_FILE_ENCODING', 'UTF-8')

    # Extract the default secrets directory path from the environment if defined, otherwise use the default path
    if secrets_path is None:
        secrets_path = os.getenv('ADP_ENV_SECRETS_DIR', DEFAULT_SECRETS_PATH)

    params: dict = {
        '_env_file': env_file_path,
        '_env_file_encoding': env_file_encoding,
    }

    os.putenv('ADP_ENV_FILE', str(env_file_path))
    os.putenv('ADP_ENV_FILE_ENCODING', env_file_encoding)

    if secrets_path is not None:
        valid: bool = True

        if not os.path.exists(secrets_path):
            valid = False
            print(f'The given path for the "--secrets-dir" option does not exist: {secrets_path}')
        elif not os.path.isdir(secrets_path):
            valid = False
            print(f'The given path for the "--secrets-dir" option is not a directory: {secrets_path}')

        if valid:
            params['_secrets_dir'] = secrets_path
            os.putenv('ADP_ENV_SECRETS_DIR', str(secrets_path))

    # Load base app configuration settings from the given environment file and the local environment
    app_settings = AppSettings(**params)

    # Load additional configuration from the given YAML configuration file (if any)
    if app_settings.config_path is not None:
        if not app_settings.config_path.startswith('/'):
            app_settings.config_path = os.path.join(app_settings.root_path, app_settings.config_path)
        app_settings = load_config(app_settings)

    return app_settings


def load_config(app_settings: AppSettings) -> AppSettings:
    """ Loads the app's configuration from the given configuration file. """
    from yaml import YAMLError

    config_path: str | None = app_settings.config_path

    if not isinstance(config_path, str):
        return app_settings

    if len(config_path.strip()) == 0:
        return app_settings

    if not config_path.startswith('/'):
        config_path = os.path.join(app_settings.root_path, config_path)

    try:
        with open(config_path, 'r') as f:
            app_settings.config = yaml.load(f, Loader=yaml.FullLoader)
            f.close()
    except FileNotFoundError:
        # print(f'The given path for the configuration file does not exist: {config_path}')
        pass
    except IsADirectoryError:
        # print(f'The given path for the configuration file is not a file: {config_path}')
        pass
    except PermissionError:
        # print(f'Permission denied when trying to read the configuration file: {config_path}')
        pass
    except UnicodeDecodeError:
        # print(f'Failed to decode the configuration file: {config_path}')
        pass
    except YAMLError as e:
        # print(f'Failed to parse the configuration file "{config_path}": {e}')
        pass

    return app_settings


def save_config(app_settings: AppSettings, config: dict[str, any]) -> bool:
    """ Saves the app's configuration to the defined configuration file setting path. """

    config_path: str = app_settings.config_path

    if not config_path.startswith('/'):
        config_path = os.path.join(app_settings.root_path, config_path)

    with open(config_path, 'w') as f:
        yaml.dump(config, f)
        f.close()

    return True


# Load application settings from the environment and environment configuration files
settings: AppSettings = load_settings()
