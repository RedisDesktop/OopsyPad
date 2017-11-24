import click

import requests

from oopsypad.client.base import oopsy, get_address


@oopsy.group(name='oopsy_admin')
@click.pass_context
def oopsy_admin(ctx):
    get_address(ctx)


@oopsy_admin.group(name='project')
def project():
    pass


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