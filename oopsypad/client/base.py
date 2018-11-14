import base64
import configparser
import os

import click
import requests
import urllib3


OOPSY_CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.oopsy')


def get_address(ctx=None):
    address = os.environ.get('OOPSY_HOST')
    if not address:
        raise click.ClickException(
            'OOPSY_HOST environment variable was not specified.')
    if ctx:
        ctx.obj = dict()
        ctx.obj['ADDRESS'] = address
    return address


def save_token(token):
    config = configparser.ConfigParser()
    config['oopsypad'] = {}
    config['oopsypad']['token'] = token
    with open(OOPSY_CONFIG_PATH, 'w') as configfile:
        config.write(configfile)


def get_token():
    config = configparser.ConfigParser()
    config.read(OOPSY_CONFIG_PATH)
    if 'oopsypad' in config:
        if 'token' in config['oopsypad']:
            token = config['oopsypad']['token']
            return base64.b64encode(token.encode())
    raise click.ClickException('Missing auth token.\n'
                               'To login use \033[33moopsy_admin login\033[0m')


class OopsyGroup(click.Group):
    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except urllib3.exceptions.NewConnectionError as e:
            click.echo('Cannot connect to server ({}).'.format(e))
        except requests.exceptions.MissingSchema as e:
            click.echo('Invalid address ({}).'.format(e))
        except click.ClickException as e:
            click.echo('{}'.format(e))


@click.group(name='oopsy', cls=OopsyGroup)
def oopsy():
    pass
