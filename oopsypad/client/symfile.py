import click
import os
import requests
import shutil
import subprocess

from oopsypad.server.config import Config

DUMP_SYMS_PATH = '3rdparty/breakpad/src/tools/linux/dump_syms/dump_syms'
DUMP_SYMS = os.path.join(Config.ROOT_DIR, DUMP_SYMS_PATH)


def create_symfile(bin_path, symfile_name, symfile_root):
    dump_syms_output = subprocess.check_output([DUMP_SYMS, bin_path], stderr=subprocess.DEVNULL)
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


@click.command(name='oopsy_send_symfile')
@click.argument('bin-path')
@click.argument('symfile-name')
@click.argument('address')
@click.argument('version')
def oopsy_send_symfile(bin_path, symfile_name, address, version):
    """
    \b
    BIN-PATH
        Product executable binary path.
    SYMFILE-NAME
        Target symbol file name.
    ADDRESS
        OopsyPad host address.
    VERSION
        Product version.
    """
    response = send_symfile(bin_path, symfile_name, address, version)
    print(response.text)


def send_symfile(bin_path, symfile_name, address, version):
    symfile_path = create_symfile(bin_path, symfile_name, Config.SYMFILES_DIR)
    with open(symfile_path, 'r') as f:
        _, platform, _, id, product = f.readline().split()
    with open(symfile_path, 'rb') as f:
        files = {'symfile': f}
        data = {'version': version, 'platform': platform}
        r = requests.post("{}/data/symfiles/{}/{}".format(address, product, id), data=data, files=files)
    return r
