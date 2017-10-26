import click
from flask import Flask, jsonify, request
import flask_mongoengine as mongo

from oopsypad.server import models
from oopsypad.server.admin import admin


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    app.config.from_envvar("OOPSYPAD_SETTINGS", silent=True)
    app.config.from_pyfile("config_local.py", silent=True)
    mongo.MongoEngine(app)
    admin.init_app(app)
    return app


app = create_app()


# Supported API
#
# Send Crash Report
# POST /crash-report
@app.route('/crash-report', methods=['POST'])
def add_minidump():
    data = request.form
    product = data['product']

    try:
        project = models.Project.objects.get(name=product)
    except Exception as e:
        return jsonify({"error": "{} is not in the projects list ({}).".format(product, e)}), 400

    version = data['version']
    if version < project.min_version:
        return jsonify({
            "error": "You use an old version. Please download at least {} release.".format(project.min_version)}), 400

    platform = data['platform']
    if platform not in project.get_allowed_platforms():
        return jsonify({"error": "{} platform is not allowed for {}".format(platform, product)}), 400
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


@click.command()
@click.option('--host', '-h', help='OopsyPad host.')
@click.option('--port', '-p', default=5000, help='OopsyPad port.')
def run_server(host, port):
    app.run(host, int(port))


if __name__ == '__main__':
    app.run()
    # app.run(debug=False)
