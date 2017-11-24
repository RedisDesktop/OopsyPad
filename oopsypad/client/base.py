import click
import os
import requests
import urllib3


def get_address(ctx=None):
    address = os.environ.get('OOPSY_HOST')
    if not address:
        raise click.UsageError('OOPSY_HOST environment variable was not specified.')
    if ctx:
        ctx.obj = dict()
        ctx.obj['ADDRESS'] = address
    return address


class OopsyGroup(click.Group):
    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except urllib3.exceptions.NewConnectionError as e:
            click.echo('Unable to connect to server ({}).'.format(e))
        except requests.exceptions.MissingSchema as e:
            click.echo('Invalid address ({}).'.format(e))
        except click.UsageError as e:
            click.echo('Error: {}'.format(e))


@click.group(name='oopsy', cls=OopsyGroup)
def oopsy():
    pass
