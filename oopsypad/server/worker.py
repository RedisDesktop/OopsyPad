from celery import Celery
from celery.utils.log import get_task_logger

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

logger = get_task_logger(__name__)


@celery.task
def process_minidump(minidump_id):
    logger.warning('Processing minidump {}...'.format(minidump_id))

    minidump = models.Minidump.get_by_id(minidump_id)
    if not minidump:
        logger.warning('Minidump {} was not found.'.format(minidump_id))
        return
    minidump.get_stacktrace()
    minidump.parse_stacktrace()
    logger.info('Minidump {} was processed.'.format(minidump_id))
