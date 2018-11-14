from flask import (after_this_request, Blueprint, current_app, jsonify, request,
                   flash, redirect)
from flask_security import current_user, http_auth_required
from flask_security.utils import (get_post_register_redirect, hash_password,
                                  login_user, url_for_security)
from flask_security.views import _commit
from werkzeug.local import LocalProxy

from oopsypad.server import models
from oopsypad.server.forms import AdminRegisterForm

bp = Blueprint('public', __name__)


def client_error(error):
    return jsonify(error=error), 400


@bp.route('/token', methods=['GET'])
@http_auth_required
def get_auth_token():
    return jsonify(token=current_user.auth_token)


@bp.route('/crash-report', methods=['POST'])
def crash_report():
    data = request.form

    product = data.get('product')
    if not product:
        return client_error('Product name is required.')

    version = data.get('version')
    if not version:
        return client_error('Product version is required.')

    platform = data.get('platform')
    if not platform:
        return client_error('Product platform is required.')

    minidump = request.files.get('upload_file_minidump')
    if not minidump:
        return client_error('Minidump file is required.')

    project = models.Project.objects(name=product).first()
    if not project:
        return client_error('{} project not found.'.format(product))

    if project.min_version and version < project.min_version:
        return client_error(
            'You use an old version. Please download at least {} '
            'release.'.format(project.min_version))

    if platform not in project.get_allowed_platforms():
        return client_error('{} platform is not allowed for {}.'.format(
            platform, product))

    try:
        models.Minidump.create_minidump(product=product,
                                        version=version,
                                        platform=platform,
                                        minidump_file=minidump)
    except Exception as e:
        error = 'Cannot save crash report: {}'.format(e)
        current_app.logger.exception(error)
        return jsonify(error=error), 500

    return jsonify(ok='Thank you!'), 201


_security = LocalProxy(lambda: current_app.extensions['security'])
_datastore = LocalProxy(lambda: _security.datastore)


def register_admin(**kwargs):
    kwargs['password'] = hash_password(kwargs['password'])
    kwargs['roles'] = ['admin']
    user = _datastore.create_user(**kwargs)
    _datastore.commit()
    return user


@bp.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    if models.User.objects.count() > 0:
        flash('Admin is already created.', 'warning')
        return redirect(url_for_security('login'))

    form_data = request.form

    form = AdminRegisterForm(form_data)

    if form.validate_on_submit():
        user = register_admin(**form.to_dict())
        form.user = user

        after_this_request(_commit)
        login_user(user)

        redirect_url = get_post_register_redirect()

        return redirect(redirect_url)

    return _security.render_template('security/setup_admin.html',
                                     setup_admin_form=form)
