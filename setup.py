from setuptools import find_packages, setup
import sys

assert sys.version_info >= (3,), 'Python 3 is required'

VERSION = '0.1.0-alpha'

setup(
    name="oopsypad",
    version=VERSION,
    description='Breakpad minidump processing tool.',
    license='GPLv3',
    install_requires=[
        'flask',
        'flask-admin',
        'flask-mongoengine',
        'redis',
        'celery',
        'python-dateutil',
        'gunicorn',
        'requests',
    ],
    tests_require=[
        'selenium',
        'flask-testing',
    ],
    test_suite='oopsypad.tests',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts':
            ['oopsy_run_server = oopsypad.server.run:run_server',
             'oopsy_send_symfile = oopsypad.client.symfile:upload_symfile',
             'oopsy_send_minidump = oopsypad.client.minidump:upload_minidump']
    }
)
