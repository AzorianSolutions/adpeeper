from setuptools import setup

setup(
    name='adpeeper',
    version='0.1.0',
    package_dir={'': 'src'},
    install_requires=[
        'jsonpickle==3.0.1',
        'loguru==0.7.0',
        'pyad==0.6.0',
        'pyyaml==6.0',
        'pydantic==1.10.2',
        'pydantic[email]',
        'python-dotenv==0.21.0',
        'pywin32',
    ],
)