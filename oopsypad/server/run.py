import subprocess

import click

from oopsypad.server.app import create_app

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
GUNICORN_WORKERS = 4

app = create_app()


@click.command(name='oopsy_run_server',
               context_settings=dict(ignore_unknown_options=True))
@click.option('--host', '-h', default=DEFAULT_HOST,
              help='OopsyPad host (default is {}).'.format(DEFAULT_HOST))
@click.option('--port', '-p', default=DEFAULT_PORT,
              help='OopsyPad port (default is {}).'.format(DEFAULT_PORT))
@click.option('--workers', '-w', default=GUNICORN_WORKERS,
              help='Gunicorn workers (default is {}).'.format(GUNICORN_WORKERS))
@click.argument('gunicorn-options', nargs=-1, type=click.UNPROCESSED)
def oopsy_run_server(host, port, workers, gunicorn_options):
    app.logger.info('Running OopsyPad from {}.'.format(app.root_path))
    subprocess.run(['gunicorn',
                    '-w {}'.format(workers),
                    '-b {}:{}'.format(host, port),
                    'oopsypad.server.run:app'] + list(gunicorn_options))
