import logging
import os
import signal
import subprocess
from time import sleep

from celery import Celery
import click
import raven
from raven.contrib.celery import register_signal, register_logger_signal

from oopsypad.server import models
from oopsypad.server.run import app

CELERY_LOG = os.path.join(app.config['ROOT_DIR'], 'celery.log')
CELERYD_PID = os.path.join(app.config['ROOT_DIR'], 'celeryd.pid')


def make_celery(app):
    celery = Celery(app.import_name,
                    backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)

logger = logging.getLogger(__name__)


@celery.on_after_configure.connect
def setup_tasks(sender, **kwargs):
    with app.app_context():
        if app.config.get('ENABLE_SENTRY'):
            client = raven.Client(
                app.config['SENTRY_DSN'])
            register_logger_signal(client, logger=logger)
            register_signal(client)


@celery.task
def process_minidump(minidump_id):
    logger.info('Processing minidump {}...'.format(minidump_id))

    minidump = models.Minidump.get_by_id(minidump_id)
    if not minidump:
        logger.error('Minidump {} was not found.'.format(minidump_id))
        return
    minidump.get_stacktrace()
    minidump.parse_stacktrace()
    logger.info('Minidump {} was processed.'.format(minidump_id))


@click.group('oopsy_celery_worker')
def oopsy_celery_worker():
    pass


@oopsy_celery_worker.command('run')
def oopsy_celery_worker_run():
    if os.path.isfile(CELERYD_PID):
        if click.confirm('Celery worker is already running. Restart?',
                         default=True):
            terminate_celery_worker()
            click.echo('Restarting...')
    while os.path.isfile(CELERYD_PID):
        sleep(.25)
    subprocess.run(['celery', 'worker', '-A', 'oopsypad.server.worker.celery',
                    '--detach', '--loglevel', 'info', '--logfile', CELERY_LOG,
                    '--pidfile', CELERYD_PID])
    click.echo('Celery worker is running.')


def terminate_celery_worker():
    try:
        with open(CELERYD_PID) as pid:
            os.kill(int(pid.read()), signal.SIGTERM)
            click.echo('Celery worker process was terminated.')
    except OSError:
        click.echo('Celery worker is not running.')


@oopsy_celery_worker.command('stop')
def oopsy_celery_worker_stop():
    terminate_celery_worker()


@oopsy_celery_worker.command('logs')
@click.option('--number', '-n', default=0, type=int, help='Show last n entries.')
def oopsy_celery_worker_logs(number):
    try:
        with open(CELERY_LOG) as logs:
            for line in logs.readlines()[-number:]:
                click.echo(line)
    except OSError:
        click.echo('No logfile found.')
