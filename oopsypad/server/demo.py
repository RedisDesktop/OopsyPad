import datetime

from flask_security.utils import hash_password

from oopsypad.server import security


def create_test_user():
    try:
        security.user_datastore.find_or_create_role(name='admin')
        if not security.user_datastore.find_user(email='test@test.com'):
            security.user_datastore.create_user(
                email='test@test.com',
                password=hash_password('test'),
                auth_token='test',
                confirmed_at=datetime.datetime.now(),
                roles=['admin']
            )
    except Exception as e:
        print(e)
