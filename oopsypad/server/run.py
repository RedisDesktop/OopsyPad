import click
import os
from oopsypad.server import app
import subprocess


@click.command()
@click.option('--host', '-h', default="127.0.0.1", help='OopsyPad host.')
@click.option('--port', '-p', default=5000, help='OopsyPad port.')
def run_server(host, port):
    os.chdir(app.root_path)
    subprocess.run(['gunicorn',
                    '-w 4',
                    '-b {}:{}'.format(host, port),
                    'views:app'])
