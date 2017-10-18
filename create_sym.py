import click
import os
import requests
import shutil
import subprocess

rdm_path = "/usr/share/redis-desktop-manager/bin/rdm"
sym_file_name = "rdm.sym"
sym_file_root = "symbols"


def create_sym_file(bin_path, sym_file_name, sym_file_root):
    dump_syms_output = subprocess.run(['dump_syms', bin_path], stdout=subprocess.PIPE)
    with open(sym_file_name, 'wb') as f:
        f.write(dump_syms_output.stdout)

    with open(sym_file_name, 'r') as f:
        module_info = f.readline().split()

    sym_file_id, sym_file_app = module_info[3], module_info[4]

    sym_file_target_path = os.path.join(sym_file_root, sym_file_app, sym_file_id)

    if not os.path.isdir(sym_file_target_path):
        os.makedirs(sym_file_target_path)
    sym_file_path = os.path.join(sym_file_target_path, sym_file_name)
    shutil.move(sym_file_name, sym_file_path)
    return sym_file_path


@click.command()
@click.option('--path', help='Binary path.')
@click.option('--name', help='Target symbol file name.')
@click.option('--address', help='Host address.')
@click.option('--version', help='Product version.')
def upload_sym_file(path, name, address, version):
    sym_file_path = create_sym_file(path, name, sym_file_root)
    with open(sym_file_path, 'rb') as f:
        files = {'symfile': f}
        data = {'version': version}
        requests.post("{}/sym-file".format(address), data=data, files=files)


def send_sym_file():
    create_sym_file(rdm_path, sym_file_name, sym_file_root)
    address = "http://127.0.0.1:5000"
    with open(sym_file_name, 'rb') as f:
        files = {'symfile': f}
        data = {'version': '0.8.0'}
        r = requests.post(url="{}/sym-file".format(address), data=data, files=files)
    return r


if __name__ == '__main__':
    upload_sym_file()
