import os
import shutil
import subprocess

import click
import requests

from oopsypad.client.base import oopsy, get_address, get_token
from oopsypad.server.config import Config

DUMP_SYMS_PATH = '3rdparty/breakpad/src/tools/linux/dump_syms/dump_syms'
DUMP_SYMS = os.path.join(Config.ROOT_DIR, DUMP_SYMS_PATH)


def create_symfile(bin_path, symfile_name, symfile_root):
    dump_syms_output = subprocess.check_output(
        [DUMP_SYMS, bin_path], stderr=subprocess.DEVNULL)
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


@oopsy.command(name='oopsy_send_symfile')
@click.argument('bin-path')
@click.argument('symfile-name')
@click.argument('version')
def oopsy_send_symfile(bin_path, symfile_name, version):
    """
    \b
    BIN-PATH
        Product executable binary path.
    SYMFILE-NAME
        Target symbol file name.
    VERSION
        Product version.
    """
    response = send_symfile(bin_path, symfile_name, get_address(), version)
    if response.status_code == 201:
        click.echo(response.json().get('ok', 'OK'))
    elif response.status_code == 403:
        click.echo(response.reason.capitalize())
    else:
        click.echo(response.json().get('error', 'ERROR'))


def send_symfile(bin_path, symfile_name, address, version):
    symfile_path = create_symfile(bin_path, symfile_name, Config.SYMFILES_DIR)
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
