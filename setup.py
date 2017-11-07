import os
from setuptools import find_packages, setup
import sys

assert sys.version_info >= (3,), 'Python 3 is required'

VERSION = '0.1.0-alpha'
if sys.argv[-1] == 'install':
    os.system('./3rdparty/build.sh')

setup(
    name="oopsypad",
    version=VERSION,
    description='Breakpad minidump processing tool.',
    install_requires=[
        'flask',
        'flask-admin',
        'flask-mongoengine',
        'redis',
        'celery',
        'python-dateutil',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts':
            ['oopsy_run_server = oopsypad.server.app:run_server',
             'oopsy_send_symfile = oopsypad.client.symfile:upload_symfile',
             'oopsy_send_minidump = oopsypad.client.minidump:upload_minidump']
    }
)
