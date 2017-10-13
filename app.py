from flask import Flask, jsonify, request
import flask_mongoengine as mongo
import json
import models


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1MB
    app.config['DEBUG'] = True
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
    # > curl http://127.0.0.1:5000/crash-report -F minidump=@/home/mrn/7b6adef3-9734-0904-02f96cac-28733638.dmp
    # -F data='{"product":"RedisDesktopManager","version":"0.8.0","platform":"Linux"}'
    data = json.loads(request.form['data'])
    version = data['version']

    if version < "0.8":
        return jsonify({
            "error": "You use an old version. "
                     "Please download the latest release <a href=\"http://redisdesktop.com/download\">0.8.0</a>"}
        ), 400

    models.Minidump.create_minidump(request)

    return jsonify({"ok": "Thank you!"}), 201


@app.route('/sym-file', methods=['POST'])
def add_sym_file():
    raise NotImplementedError()


if __name__ == '__main__':
    app.run()
