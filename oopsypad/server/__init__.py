from flask import Blueprint, jsonify, request
from flask_security import (current_user, login_required, http_auth_required,
                            roles_accepted)

from oopsypad.server import models


api_bp = Blueprint('oopsypad_api', __name__)
public_bp = Blueprint('oopsypad', __name__)


@public_bp.route('/token', methods=['GET'])
@http_auth_required
def get_auth_token():
    return jsonify(token=current_user.auth_token)


@public_bp.route('/crash-report', methods=['POST'])
def crash_report():
    data = request.form

    product = data.get('product')
    if not product:
        return jsonify(error='Product name is required.')
    project = models.Project.objects(name=product).first()
    if not project:
        return jsonify(error='{} project does not exist.'.format(product)), 400

    version = data.get('version')
    if not version:
        return jsonify(error='Product version is required.')
    if version < project.min_version:
        return jsonify(
            error='You use an old version. Please download at least {} '
                  'release.'.format(project.min_version)), 400

    platform = data.get('platform')
    if not platform:
        return jsonify(error='Product platform is required.')
    if platform not in project.get_allowed_platforms():
        return jsonify(error='{} platform is not allowed for {}.'.format(
            platform, product)), 400
    minidump = request.files.get('upload_file_minidump')
    if not minidump:
        return jsonify(error='Minidump file is required.')
    try:
        models.Minidump.create_minidump(product=product,
                                        version=version,
                                        platform=platform,
                                        minidump_file=minidump)
    except Exception as e:
        return jsonify(error='Something went wrong: {}'.format(e)), 400

    return jsonify(ok='Thank you!'), 201


@api_bp.route('/data/symfile/<product>/<id>', methods=['POST'])
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


@api_bp.route('/projects/<name>', methods=['POST'])
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


@api_bp.route('/projects/<name>/delete', methods=['DELETE'])
@login_required
@roles_accepted('admin')
def delete_project(name):
    try:
        models.Project.objects.get(name=name).delete()
        return jsonify(ok='{} project was deleted.'.format(name)), 202
    except Exception as e:
        return jsonify(error='Something went wrong: {}'.format(e)), 400


@api_bp.route('/projects')
@login_required
@roles_accepted('admin')
def list_projects():
    try:
        projects = [models.Project.get_project_dict(p)
                    for p in models.Project.objects()]
        return jsonify(projects=projects), 200
    except Exception as e:
        return jsonify(error='Something went wrong: {}'.format(e)), 400
