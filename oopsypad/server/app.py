from celery import Celery
from flask import Flask, jsonify, request
import flask_mongoengine as mongo
import subprocess

from oopsypad.server import models


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    app.config.from_pyfile("config_local.py", silent=True)
    mongo.MongoEngine(app)
    return app


app = create_app()
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


# Supported API
#
# Send Crash Report
# POST /crash-report
@app.route('/crash-report', methods=['GET', 'POST'])
def add_minidump():
    if request.method == 'POST':
        # NOTE (COMMAND EXAMPLE TO CHECK):
        # curl <site_host>/crash-report -F upload_file_minidump=@/path/to/dump_file
        # -F product=<product> -F version=<version> -F platform=<platform>
        data = request.form
        version = data['version']
        if version < "0.8":
            return jsonify({
                "error": "You use an old version. "
                         "Please download the latest release <a href=\"http://redisdesktop.com/download\">0.8.0</a>"}
            ), 400
        try:
            minidump = models.Minidump.create_minidump(request)
            process_minidump.delay(str(minidump.id))
        except Exception as e:
            return jsonify({"error": "Something went wrong: {}".format(e)}), 400

        return jsonify({"ok": "Thank you!"}), 201
    else:
        return jsonify({"ok": "Try POST"})


@app.route('/data/symfiles/<product>/<id>', methods=['GET', 'POST'])
def add_symfile(product, id):
    if request.method == 'POST':
        try:
            models.SymFile.create_symfile(request, product, id)
            return jsonify({"ok": "Symbol file saved."}), 201
        except Exception as e:
            return jsonify({"error": "Something went wrong: {}".format(e)}), 400
    else:
        return jsonify({"ok": "Try POST"})


if __name__ == '__main__':
    app.run()
