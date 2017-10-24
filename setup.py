from setuptools import find_packages, setup
import sys

assert sys.version_info >= (3,), 'Python 3 is required'

VERSION = "0.1"

setup(
    name="oopsypad",
    version=VERSION,
    description='Breakpad minidump processing tool.',
    install_requires=[
        'flask',
        'flask-mongoengine',
        'redis',
        'celery',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts':
            ['oopsy_send_symfile = oopsypad.client.symfile:upload_symfile',
             'oopsy_send_minidump = oopsypad.client.minidump:upload_minidump']
    }
)
