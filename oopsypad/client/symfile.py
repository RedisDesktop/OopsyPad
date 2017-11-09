import click
import os
import requests
import shutil
import subprocess

from oopsypad.server.views import app


def create_symfile(bin_path, symfile_name, symfile_root):
    dump_syms_output = subprocess.run(['dump_syms', bin_path], stdout=subprocess.PIPE)
    with open(symfile_name, 'wb') as f:
        f.write(dump_syms_output.stdout)

    with open(symfile_name, 'r') as f:
        _, _, _, id, product = f.readline().split()

    symfile_target_path = os.path.join(symfile_root, product, id)

    if not os.path.isdir(symfile_target_path):
        os.makedirs(symfile_target_path)
    symfile_path = os.path.join(symfile_target_path, symfile_name)
    shutil.move(symfile_name, symfile_path)
    return symfile_path


@click.command()
@click.argument('path')
@click.argument('name')
@click.argument('address')
@click.argument('version')
def upload_symfile(path, name, address, version):
    """
    \b
    PATH
        Product executable binary path.
    NAME
        Target symbol file name.
    ADDRESS
        OopsyPad host address.
    VERSION
        Product version.
    """
    response = send_symfile(path, name, address, version)
    print(response.text)


def send_symfile(path, name, address, version):
    symfile_path = create_symfile(path, name, app.config['SYMFILES_DIR'])
    with open(symfile_path, 'r') as f:
        _, platform, _, id, product = f.readline().split()
    with open(symfile_path, 'rb') as f:
        files = {'symfile': f}
        data = {'version': version, 'platform': platform}
        r = requests.post("{}/data/symfiles/{}/{}".format(address, product, id), data=data, files=files)
    return r
