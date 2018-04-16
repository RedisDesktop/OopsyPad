import click
import requests

from oopsypad.client.base import oopsy, get_address


@oopsy.command(name='oopsy_crash_report')
@click.argument('dump-path')
@click.argument('product')
@click.argument('version')
@click.argument('platform')
def oopsy_crash_report(dump_path, product, version, platform):
    """
    \b
    DUMP-PATH
        Minidump file path.
    PRODUCT
        Product name.
    VERSION
        Product version.
    PLATFORM
        Platform that the product is running on (Linux, MacOS, Windows).
    """
    response = send_crash_report(
        get_address(), dump_path, product, version, platform)
    if response.status_code == 201:
        click.echo(response.json().get('ok', 'OK'))
    else:
        click.echo(response.json().get('error', 'ERROR'))


def send_crash_report(address, dump_path, product, version, platform):
    with open(dump_path, 'rb') as f:
        data = {'product': product, 'version': version, 'platform': platform}
        files = {'upload_file_minidump': f}
        response = requests.post(
            '{}/crash-report'.format(address), data=data, files=files)
    return response
