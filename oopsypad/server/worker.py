from celery import Celery

import flask_mongoengine as mongo

from oopsypad.server import models
from oopsypad.server.run import app


def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
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


@celery.task
def process_minidump(minidump_id):
    try:
        minidump = models.Minidump.get_by_id(minidump_id)
        minidump.get_stacktrace()
        minidump.parse_stacktrace()
        print("Minidump {} processed.".format(minidump_id))
    except mongo.DoesNotExist:
        print("Minidump with id {} was not found.".format(minidump_id))
