from flask import Blueprint, jsonify, request
from flask_security import login_required, roles_accepted

from oopsypad.server import models

bp = Blueprint('api', __name__)


@bp.route('/data/symfile/<product>/<id>', methods=['POST'])
@login_required
@roles_accepted('admin', 'sym_uploader')
def add_symfile(product, id):
    data = request.form
    version = data.get('version')
    platform = data.get('platform')
    symfile = request.files.get('symfile')

    try:
        models.Symfile.create_symfile(product=product,
                                      version=version,
                                      platform=platform,
                                      file=symfile,
                                      symfile_id=id)
        return jsonify(ok='Symbol file was saved.'), 201
    except Exception as e:
        return jsonify(error='Something went wrong: {}'.format(e)), 400


@bp.route('/projects/<name>', methods=['POST'])
@login_required
@roles_accepted('admin')
def add_project(name):
    try:
        project = models.Project.create_project(name=name)

        min_version = request.json.get('min_version')
        if min_version:
            project.update_min_version(min_version)

        allowed_platforms = request.json.get('allowed_platforms')
        if allowed_platforms:
            for p in allowed_platforms:
                platform = models.Platform.create_platform(p)
                project.add_allowed_platform(platform)

        return jsonify(ok='Project was saved. \n{}'.format(project)), 201
    except Exception as e:
        return jsonify(error='Something went wrong: {}'.format(e)), 400


@bp.route('/projects/<name>/delete', methods=['DELETE'])
@login_required
@roles_accepted('admin')
def delete_project(name):
    try:
        project = models.Project.objects(name=name).first()
        if not project:
            return jsonify(error='Project not found.'), 400

        project.delete()
        return jsonify(ok='{} project was deleted.'.format(name)), 202
    except Exception as e:
        return jsonify(error='Something went wrong: {}'.format(e)), 400


@bp.route('/projects')
@login_required
@roles_accepted('admin')
def list_projects():
    try:
        projects = [models.Project.get_project_dict(p)
                    for p in models.Project.objects()]
        return jsonify(projects=projects), 200
    except Exception as e:
        return jsonify(error='Something went wrong: {}'.format(e)), 400
