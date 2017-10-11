import glob
import os
import subprocess

home_dir = os.path.expanduser('~')
dump_path = glob.glob(os.path.join(home_dir, '*.dmp'))[0]
symbols_path = os.path.join(os.getcwd(), "symbols")
minidump_stackwalk_output = subprocess.run(['minidump_stackwalk', dump_path, symbols_path], stdout=subprocess.PIPE)
with open('rdm_stacktrace.txt', 'wb') as f:
    f.write(minidump_stackwalk_output.stdout)
