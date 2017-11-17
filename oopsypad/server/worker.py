from celery import Celery
from oopsypad.server import app, models

_celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])


@_celery.task
def process_minidump(minidump_id):
    with app.app_context():
        minidump = models.Minidump.objects.get(id=minidump_id)
        minidump.get_stacktrace()
        minidump.parse_stacktrace()