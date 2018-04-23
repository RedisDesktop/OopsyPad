import logging
from logging.handlers import RotatingFileHandler
import os

from flask import Flask, jsonify, render_template, request
from flask_security import Security
from raven.contrib.flask import Sentry

from oopsypad.server import api_bp, public_bp, config
from oopsypad.server.admin import admin
from oopsypad.server.demo import create_test_users
from oopsypad.server.models import db, User
from oopsypad.server.security import user_datastore, load_security_extensions


def create_app(config_name=None):
    if not config_name:
        env = os.getenv('OOPSY_ENV', config.PROD).lower()
        if env in config.app_config:
            config_name = env
        else:
            print('"{}" env is not supported, running on "{}".'.format(
                env, config.PROD))

    app = Flask(__name__)

    # Setup config
    app.config.from_object(config.app_config[config_name])
    app.config.from_envvar('OOPSYPAD_SETTINGS', silent=True)
    app.config.from_pyfile('config_local.py', silent=True)

    # Setup extensions
    db.init_app(app)
    admin.init_app(app)
    security = Security(app, user_datastore)

    # Setup security
    load_security_extensions(app)

    @security.register_context_processor
    def security_register_processor():
        if User.objects.count() == 0:
            return {'setup_admin': True}
        return {}

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(public_bp)

    # Setup logging
    handler = RotatingFileHandler(
        'oopsy.log', maxBytes=1024 * 1024 * 100, backupCount=10)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Setup Sentry
    if app.config['ENABLE_SENTRY']:
        Sentry(app, dsn=app.config['SENTRY_DSN'],
               logging=True, level=logging.ERROR)

    # Create user roles
    with app.app_context():
        user_datastore.find_or_create_role(name='admin')
        user_datastore.find_or_create_role(name='developer')
        user_datastore.find_or_create_role(name='sym_uploader')
        # Create test user
        if app.config['CREATE_TEST_USERS']:
            create_test_users()

    # Setup error handlers
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api'):
            return jsonify(error='Not Found'), 404
        return render_template('404.html', error=e)

    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith('/api'):
            return jsonify(error='Internal Server Error'), 500
        return render_template('500.html', error=e)

    return app


if __name__ == '__main__':
    app = create_app(config_name=config.DEV)
    app.run()
