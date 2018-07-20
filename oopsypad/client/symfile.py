import os
import shutil
import subprocess

import click
import requests

from oopsypad.client.base import oopsy, get_address, get_token
from oopsypad.server.config import Config


def create_symfile(bin_path, symfile_name, symfile_root):
    dump_syms_output = subprocess.check_output(
        [Config.DUMP_SYMS, bin_path], stderr=subprocess.DEVNULL)
    with open(symfile_name, 'wb') as f:
        f.write(dump_syms_output)

    with open(symfile_name, 'r') as f:
        _, _, _, id, product = f.readline().split()

    symfile_target_path = os.path.join(symfile_root, product, id)

    if not os.path.isdir(symfile_target_path):
        os.makedirs(symfile_target_path)
    symfile_path = os.path.join(symfile_target_path, symfile_name)
    shutil.move(symfile_name, symfile_path)
    return symfile_path


def send_symfile(symfile_path, address, version):
    with open(symfile_path, 'r') as f:
        _, platform, _, id, product = f.readline().split()
    with open(symfile_path, 'rb') as f:
        headers = {'Authorization': get_token()}
        data = {'version': version, 'platform': platform}
        files = {'symfile': f}
        r = requests.post(
            '{}/api/data/symfile/{}/{}'.format(address, product, id),
            data=data, headers=headers, files=files)
    return r


@oopsy.group('oopsy_symfile')
def oopsy_symfile():
    pass


@oopsy_symfile.command(name='create')
@click.argument('bin-path')
@click.argument('symfile-name')
def oopsy_symfile_create(bin_path, symfile_name):
    """
    \b
    BIN-PATH
        Product executable binary path.
    SYMFILE-NAME
        Target symbol file name.
    """
    symfile_path = create_symfile(bin_path, symfile_name, Config.SYMFILES_DIR)
    click.echo(symfile_path)


@oopsy_symfile.command(name='send')
@click.argument('symfile-path')
@click.argument('version')
def oopsy_symfile_send(symfile_path, version):
    """
    \b
    SYMFILE-PATH
        Path to the generated symbol file.
    VERSION
        Product version.
    """
    response = send_symfile(symfile_path, get_address(), version)
    if response.status_code == 201:
        click.echo(response.json().get('ok', 'OK'))
    elif response.status_code == 403:
        click.echo(response.reason.capitalize())
    else:
        try:
            click.echo(response.json().get('error', 'ERROR'))
        except ValueError as e:
            click.echo("Server responded %s: %s" % 
                       (response.status_code, response.content))
