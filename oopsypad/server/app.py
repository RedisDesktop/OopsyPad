from flask import Flask, jsonify, request
import flask_mongoengine as mongo

from oopsypad.server import models


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    app.config.from_envvar("OOPSYPAD_SETTINGS", silent=True)
    app.config.from_pyfile("config_local.py", silent=True)
    mongo.MongoEngine(app)
    return app


app = create_app()


# Supported API
#
# Send Crash Report
# POST /crash-report
@app.route('/crash-report', methods=['POST'])
def add_minidump():
    # NOTE (COMMAND EXAMPLE TO CHECK):
    # curl <site_host>/crash-report -F upload_file_minidump=@</path/to/dump_file>
    # -F product=<product> -F version=<version> -F platform=<platform>
    data = request.form
    version = data['version']
    if version < "0.8":
        return jsonify({
            "error": "You use an old version. "
                     "Please download the latest release <a href=\"http://redisdesktop.com/download\">0.8.0</a>"}
        ), 400
    try:
        models.Minidump.create_minidump(request)
    except Exception as e:
        return jsonify({"error": "Something went wrong: {}".format(e)}), 400

    return jsonify({"ok": "Thank you!"}), 201


@app.route('/data/symfiles/<product>/<id>', methods=['POST'])
def add_symfile(product, id):
    try:
        models.SymFile.create_symfile(request, product, id)
        return jsonify({"ok": "Symbol file saved."}), 201
    except Exception as e:
        return jsonify({"error": "Something went wrong: {}".format(e)}), 400


if __name__ == '__main__':
    app.run()
