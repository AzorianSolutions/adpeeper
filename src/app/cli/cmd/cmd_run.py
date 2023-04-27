import click
import os
import subprocess
from app.cli.start import Environment, pass_environment


@click.command("run", short_help="Run the application with the appropriate server based on the environment.")
@pass_environment
def cli(ctx: Environment):
    """ Run the application with the appropriate server based on the environment."""

    command: list = []

    if ctx.settings.server_type not in ['gunicorn', 'uvicorn', 'uwsgi']:
        print(f'Invalid server type: {ctx.settings.server_type}')
        exit(1)

    server_env = os.environ.copy()

    # Run the application with Gunicorn HTTP/WSGI server
    if ctx.settings.server_type == 'gunicorn':
        command_args: list = ['--workers=1', '--threads=1', '--timeout=0', '--log-level=info',
                              '--log-file=-', '--access-logfile=-', '--error-logfile=-', '--enable-stdio-inheritance',
                              '--capture-output', f'--bind={ctx.settings.server_address}:{ctx.settings.server_port}']

        if ctx.settings.debug:
            command_args += ['--reload-engine', 'auto']

        server_env['GUNICORN_CMD_ARGS'] = ' '.join(command_args)

        command += ['gunicorn', 'main:app']

        subprocess.run(command, env=server_env, stdout=subprocess.PIPE)

    # Run the application with Uvicorn ASGI server
    elif ctx.settings.server_type == 'uvicorn':
        command += ['uvicorn', '--host', ctx.settings.server_address, '--port', str(ctx.settings.server_port),
                    '--root-path', ctx.settings.proxy_root,
                    '--log-level', 'info', '--access-log', '--workers', '1', '--proxy-headers']

        if ctx.settings.debug:
            command += ['--reload']

        command += ['main:app']

        subprocess.run(command, env=server_env, stdout=subprocess.PIPE)

    # Run the application with UWSGI server
    elif ctx.settings.server_type == 'uwsgi':
        command += ['uwsgi', '--http-socket', f'{ctx.settings.server_address}:{ctx.settings.server_port}',
                    '--workers', '1', '--threads', '1', '--enable-threads', '--plugins', 'python3',
                    '--wsgi-file']

        command += ['main.py']

        subprocess.run(command, env=server_env, stdout=subprocess.PIPE)
