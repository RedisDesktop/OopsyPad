from flask import Flask, jsonify, request
import flask_mongoengine as mongo
import models


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB (max size of rdm sym file ever seen is 1.9 MB)
    app.config['DEBUG'] = True
    mongo.MongoEngine(app)
    return app


app = create_app()


# Supported API
#
# Send Crash Report
# POST /crash-report
@app.route('/crash-report', methods=['GET', 'POST'])
def add_minidump():
    if request.method == 'POST':
        # NOTE (COMMAND EXAMPLE TO CHECK):
        # curl <site_host>/crash-report -F minidump=@/path/to/dump_file
        # -F product=<product> -F version=<version> -F platform=<platform>
        data = request.form
        version = data['version']

        if version < "0.8":
            return jsonify({
                "error": "You use an old version. "
                         "Please download the latest release <a href=\"http://redisdesktop.com/download\">0.8.0</a>"}
            ), 400

        models.Minidump.create_minidump(request)

        return jsonify({"ok": "Thank you!"}), 201
    else:
        return jsonify({"ok": "Try POST"})


@app.route('/sym-file', methods=['GET', 'POST'])
def add_sym_file():
    # NOTE (COMMAND EXAMPLE TO CHECK):
    # > curl <site_host>/sym-file -F symfile=@/path/to/sym_file -F version=<version>
    if request.method == 'POST':
        try:
            models.SymFile.create_sym_file(request)
            return jsonify({"ok": "Symbol file saved."}), 201
        except Exception as e:
            return jsonify({"error": "Something went wrong: {}".format(e)}), 400
    else:
        return jsonify({"ok": "Try POST"})

if __name__ == '__main__':
    app.run()
