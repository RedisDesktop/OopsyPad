import glob
import os
import subprocess
from app import app


def process_minidump(dump_path, symbols_path):
    minidump_stackwalk_output = subprocess.run(
        ['minidump_stackwalk', dump_path, symbols_path], stdout=subprocess.PIPE)
    with open('rdm_stacktrace.txt', 'wb') as f:
        f.write(minidump_stackwalk_output.stdout)


if __name__ == '__main__':
    home_dir = os.path.expanduser('~')
    dump_path = glob.glob(os.path.join(home_dir, '*.dmp'))[0]
    symbols_path = os.path.join(os.getcwd(), app.config['SYMFILES_DIR'])
    process_minidump(dump_path, symbols_path)
