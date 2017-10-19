import click
import os
import requests
import shutil
import subprocess
from app import app


def create_symfile(bin_path, symfile_name, symfile_root):
    dump_syms_output = subprocess.run(['dump_syms', bin_path], stdout=subprocess.PIPE)
    with open(symfile_name, 'wb') as f:
        f.write(dump_syms_output.stdout)

    with open(symfile_name, 'r') as f:
        _, _, _, symfile_id, symfile_app = f.readline().split()

    symfile_target_path = os.path.join(symfile_root, symfile_app, symfile_id)

    if not os.path.isdir(symfile_target_path):
        os.makedirs(symfile_target_path)
    symfile_path = os.path.join(symfile_target_path, symfile_name)
    shutil.move(symfile_name, symfile_path)
    return symfile_path


@click.command()
@click.option('--path', help='Binary path.')
@click.option('--name', help='Target symbol file name.')
@click.option('--address', help='Host address.')
@click.option('--version', help='Product version.')
def upload_symfile(path, name, address, version):
    symfile_path = create_symfile(path, name, app.config['SYMFILES_DIR'])
    with open(symfile_path, 'rb') as f:
        files = {'symfile': f}
        data = {'version': version}
        requests.post("{}/sym-file".format(address), data=data, files=files)


if __name__ == '__main__':
    upload_symfile()
