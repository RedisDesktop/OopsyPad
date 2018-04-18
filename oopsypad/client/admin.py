import click
import requests

from oopsypad.client.base import oopsy, get_address, get_token, save_token


@oopsy.group(name='oopsy_admin')
@click.pass_context
def oopsy_admin(ctx):
    get_address(ctx)


@oopsy_admin.command(name='login')
@click.option('--user', '-u', prompt='Email')
@click.option('--password', '-p', prompt=True, hide_input=True)
@click.pass_context
def login(ctx, user, password):
    response = requests.get(
        '{}/token'.format(ctx.obj['ADDRESS']), auth=(user, password))
    if response.status_code == 200:
        save_token(response.json().get('token'))
        click.echo('Logged in as {}'.format(user))
    else:
        click.echo('Unauthorized')


@oopsy_admin.group(name='project')
def project():
    pass


@project.command(name='add')
@click.argument('project-name')
@click.option('--min-version', '-v', help='Project minimum allowed version.')
@click.option('--platforms', '-p', multiple=True,
              help='Allowed platforms (multiple values are acceptable, '
                   'e.g. -p <p1> -p <p2>).')
@click.pass_context
def add_project(ctx, project_name, min_version, platforms):
    headers = {'Authorization': get_token()}
    project_data = {'min_version': min_version, 'allowed_platforms': platforms}
    response = requests.post(
        '{}/api/projects/{}'.format(ctx.obj['ADDRESS'], project_name),
        json=project_data, headers=headers)
    if response.status_code == 201:
        click.echo(response.json().get('ok', 'OK'))
    elif response.status_code == 403:
        click.echo(response.reason.capitalize())
    else:
        click.echo(response.json().get('error', 'ERROR'))


@project.command(name='delete')
@click.argument('project-name')
@click.pass_context
def delete_project(ctx, project_name):
    headers = {'Authorization': get_token()}
    response = requests.delete(
        '{}/api/projects/{}/delete'.format(ctx.obj['ADDRESS'], project_name),
        headers=headers)
    if response.status_code == 202:
        click.echo(response.json().get('ok', 'OK'))
    elif response.status_code == 403:
        click.echo(response.reason.capitalize())
    else:
        click.echo(response.json().get('error', 'ERROR'))


@project.command(name='list')
@click.pass_context
def list_projects(ctx):
    headers = {'Authorization': get_token()}
    response = requests.get('{}/api/projects'.format(ctx.obj['ADDRESS']),
                            headers=headers)
    if response.status_code == 200:
        projects = response.json().get('projects')
        if projects:
            click.echo('Projects:')
            for i, p in enumerate(projects):
                click.echo('{} {}'.format(i + 1, p['name']))
                click.echo(
                    '  Minimum allowed version: {}'.format(p['min_version']))
                click.echo(
                    '  Allowed Platforms: {}'.format(
                        ', '.join(p['allowed_platforms'])))
        else:
            click.echo('No projects.')
    elif response.status_code == 403:
        click.echo(response.reason.capitalize())
    else:
        click.echo(response.json().get('error', 'ERROR'))
