import os
import shutil
import subprocess

rdm_path = "/usr/share/redis-desktop-manager/bin/rdm"
sym_file_path = "rdm.sym"

dump_syms_output = subprocess.run(['dump_syms', rdm_path], stdout=subprocess.PIPE)
with open(sym_file_path, 'wb') as f:
    f.write(dump_syms_output.stdout)

with open(sym_file_path, 'r') as f:
    module_info = f.readline().split()

sym_file_id, sym_file_app = module_info[3], module_info[4]
sym_file_root = "symbols"

sym_file_target_path = os.path.join(os.getcwd(), sym_file_root, sym_file_app, sym_file_id)

if not os.path.isdir(sym_file_target_path):
    os.makedirs(sym_file_target_path)

shutil.move(sym_file_path, os.path.join(sym_file_target_path, sym_file_path))
