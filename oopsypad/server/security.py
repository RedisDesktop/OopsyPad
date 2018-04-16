import base64

from flask import current_app, redirect, request, session, jsonify
from flask_login import utils as login_utils
from flask_security import MongoEngineUserDatastore

from oopsypad.server.models import db, User, Role

user_datastore = MongoEngineUserDatastore(db, User, Role)


def load_security_extensions(app):
    with app.app_context():
        @current_app.login_manager.request_loader
        def load_user_from_request(request):

            if request.path.startswith('/api'):
                try:
                    auth_token = request.headers.get(
                        'Authorization', '').replace('Basic ', '', 1)
                    auth_token = base64.b64decode(auth_token).decode()
                except TypeError:
                    return None

                return User.objects(auth_token=auth_token).first()
            else:
                user_id = session.get('user_id', '')

                if not user_id:
                    return None

                return User.objects(_id=user_id).first()

        @current_app.login_manager.unauthorized_handler
        def unauthorized_handler():
            if request.path.startswith("/api"):
                return jsonify(error='Unauthorized'), 401
            else:
                return redirect(
                    login_utils.login_url(
                        current_app.login_manager.login_view,
                        next_url=request.url
                    )
                )

