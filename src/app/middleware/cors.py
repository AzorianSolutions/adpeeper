from fastapi.middleware.cors import CORSMiddleware

ENVIRONMENT_KEYS: dict = {
    'ADP_CORS_ORIGINS': 'allow_origins',
    'ADP_CORS_METHODS': 'allow_methods',
    'ADP_CORS_HEADERS': 'allow_headers',
    'ADP_CORS_ALLOW_CREDENTIALS': 'allow_credentials',
}

PARAM_TYPES: dict = {
    'allow_origins': 'array',
    'allow_methods': 'array',
    'allow_headers': 'array',
    'allow_credentials': 'bool',
}


def setup(app):
    import os

    params: dict = {
        'allow_origins': ['*'],
        'allow_methods': ['*'],
        'allow_headers': ['*'],
        'allow_credentials': True,
    }

    for key, param in ENVIRONMENT_KEYS.items():
        if key in os.environ and len(str(os.environ[key]).strip()):

            if PARAM_TYPES[param] == 'array':
                params[param] = str(os.environ[key]).strip().split(',')

            if PARAM_TYPES[param] == 'bool':
                value: str = str(os.environ[key]).strip().lower()
                if value in ['true', 't', 'yes', 'y', '1', 'enabled']:
                    params[param] = True
                if value in ['false', 'f', 'no', 'n', '0', 'disabled']:
                    params[param] = False

    app.add_middleware(CORSMiddleware, **params)
