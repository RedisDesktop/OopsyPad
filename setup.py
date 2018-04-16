from setuptools import find_packages, setup
import sys

assert sys.version_info >= (3,), 'Python 3 is required'

VERSION = '0.2.1-alpha'

setup(
    name='oopsypad',
    version=VERSION,
    description='Breakpad minidump processing tool.',
    license='GPLv3',
    install_requires=[
        'flask',
        'flask-admin',
        'flask-mongoengine',
        'flask-httpauth',
        'flask-security',
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
            ['oopsy_run_server = oopsypad.server.run:oopsy_run_server',
             'oopsy_send_symfile = oopsypad.client.symfile:oopsy_send_symfile',
             'oopsy_crash_report = oopsypad.client.minidump:oopsy_crash_report',
             'oopsy_admin = oopsypad.client.admin:oopsy_admin']
    }
)
