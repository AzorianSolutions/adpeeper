from setuptools import setup

setup(
    name='adpeeper',
    version='0.1.0',
    package_dir={'': 'src'},
    install_requires=[
        'click==8.1.3',
        'cryptography==39.0.1',
        'fastapi==0.95.1',
        'fastapi-utils==0.2.1',
        'inotify==0.2.10',
        'jsonpickle==3.0.1',
        'loguru==0.7.0',
        'motor==3.1.1',
        'passlib[bcrypt]==1.7.4',
        'pyyaml==6.0',
        'pydantic==1.10.2',
        'pydantic[email]',
        'python-dotenv==0.21.0',
        'python-jose[cryptography]==3.3.0',
        'python-multipart==0.0.5',
        'requests==2.28.2',
        'uvicorn==0.20.0',
    ],
    entry_points={
        'console_scripts': [
            'adp = app.cli.start:cli',
        ],
    },
)