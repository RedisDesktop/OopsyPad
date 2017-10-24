from celery import Celery
from oopsypad.server.app import app, models
import subprocess

_celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])


@_celery.task
def process_minidump(minidump_id):
    with app.app_context():
        minidump = models.Minidump.objects.get(id=minidump_id)
        minidump_path = minidump.get_minidump_path()
        minidump_stackwalk_output = subprocess.run(['minidump_stackwalk', minidump_path,
                                                    app.config['SYMFILES_DIR']], stdout=subprocess.PIPE)
        minidump.stacktrace = minidump_stackwalk_output.stdout.decode()
        minidump.save()
