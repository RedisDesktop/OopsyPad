import logging

from celery import Celery
import raven
from raven.contrib.celery import register_signal, register_logger_signal

from oopsypad.server import models
from oopsypad.server.run import app


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
