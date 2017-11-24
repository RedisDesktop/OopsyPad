import click
import os
import requests
import urllib3


class OopsyGroup(click.Group):
    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except urllib3.exceptions.NewConnectionError as e:
            click.echo('Unable to connect to server ({}).'.format(e))
        except requests.exceptions.MissingSchema as e:
            click.echo('Invalid address ({}).'.format(e))
        except TypeError as e:
            click.echo('Error: {}'.format(e))


@click.group(name='oopsy_admin', cls=OopsyGroup)
@click.pass_context
def oopsy_admin(ctx):
    ctx.obj = {}


@oopsy_admin.group(name='project')
@click.pass_context
def project(ctx):
    address = ctx.obj['ADDRESS'] = os.environ.get('OOPSY_HOST')
    click.echo(address)
    if not address:
        raise TypeError('OOPSY_HOST variable was not specified.')


@project.command(name='add')
@click.argument('project-name')
@click.option('--min-version', '-v', help='Project minimum allowed version.')
@click.option('--platforms', '-p', multiple=True,
              help='Allowed platforms (multiple values are acceptable, e.g. -p <p1> -p <p2>).')
@click.pass_context
def add_project(ctx, project_name, min_version, platforms):
    data = {'min_version': min_version, 'allowed_platforms': platforms}
    response = requests.post('{}/project/{}'.format(ctx.obj['ADDRESS'], project_name), data=data)
    click.echo(response.text)


@project.command(name='delete')
@click.argument('project-name')
@click.pass_context
def delete_project(ctx, project_name):
    response = requests.delete('{}/project/{}/delete'.format(ctx.obj['ADDRESS'], project_name))
    click.echo(response.text)


@project.command(name='list')
@click.pass_context
def list_projects(ctx):
    response = requests.get('{}/project/all'.format(ctx.obj['ADDRESS']))
    click.echo(response.text)
