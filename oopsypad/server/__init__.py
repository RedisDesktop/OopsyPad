from flask import Flask
import flask_mongoengine as mongo
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
