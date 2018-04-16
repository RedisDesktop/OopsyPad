from flask import Flask
from flask_mongoengine import MongoEngine
import logging
from logging.handlers import RotatingFileHandler
import os

from oopsypad.server.admin import admin
from oopsypad.server.config import app_config, PROD
from oopsypad.server.views import oopsy

db = MongoEngine()


def create_app(config_name=None):
    if not config_name:
        env = os.getenv('OOPSY_ENV')
        if env:
            if env in app_config:
                config_name = env
            else:
                print("'{}' env is not supported, running on '{}'.".format(env, PROD))
                config_name = PROD
        else:
            config_name = PROD
    app = Flask(__name__)
    app.config.from_object(app_config[config_name])
    app.config.from_envvar("OOPSYPAD_SETTINGS", silent=True)
    app.config.from_pyfile("config_local.py", silent=True)
    db.init_app(app)
    admin.init_app(app)
    app.register_blueprint(oopsy)
    handler = RotatingFileHandler('oopsy.log', maxBytes=1024 * 1024 * 100, backupCount=10)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    return app


if __name__ == '__main__':
    app = create_app(config_name='dev')
    app.run()