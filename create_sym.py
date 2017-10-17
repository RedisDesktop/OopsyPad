import os
import requests
import shutil
import subprocess

rdm_path = "/usr/share/redis-desktop-manager/bin/rdm"
sym_file_name = "rdm.sym"
sym_file_root = "symbols"


def send_sym_file(path):
    with open(path, 'rb') as f:
        files = {'symfile': f}
        data = {'project': 'rdm', 'version': '0.8.0', 'platform': 'Linux'}
        r = requests.post("http://127.0.0.1:5000/sym-file", files, data)
    return r


def create_sym_file(rdm_path, sym_file_name, sym_file_root):
    dump_syms_output = subprocess.run(['dump_syms', rdm_path], stdout=subprocess.PIPE)
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


if __name__ == '__main__':
    create_sym_file(rdm_path, sym_file_name, sym_file_root)
    send_sym_file(sym_file_name)
