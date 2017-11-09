from flask import jsonify, request

from oopsypad.server import models, app


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


if __name__ == '__main__':
    app.run()

