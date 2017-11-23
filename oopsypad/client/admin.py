import click
import requests


@click.command()
@click.argument('address')
@click.argument('project-name')
@click.option('--min-version', '-v', help='Project minimum allowed version.')
@click.option('--platforms', '-p', multiple=True,
              help='Allowed platforms (multiple values are acceptable, e.g. -p <p1> -p <p2>).')
@click.option('--delete', is_flag=True, help='Delete project.')
def save_project(address, project_name, min_version, platforms, delete):
    """
    \b
    ADDRESS
        OopsyPad host address.
    PROJECT NAME
        ...
    """
    if delete:
        response = requests.delete('{}/project/{}/delete'.format(address, project_name))
    else:
        data = {'min_version': min_version, 'allowed_platforms': platforms}
        response = requests.post('{}/project/{}'.format(address, project_name), data=data)
    print(response.text)
