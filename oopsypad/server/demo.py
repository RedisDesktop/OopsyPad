import datetime

from flask_security.utils import hash_password

from oopsypad.server import security

ADMIN_TOKEN = 'admin_token'
DEV_TOKEN = 'dev_token'
SYM_TOKEN = 'sym_token'


def create_test_users():
    try:
        if not security.user_datastore.find_user(email='admin@test.com'):
            security.user_datastore.create_user(
                email='admin@test.com',
                password=hash_password('test'),
                auth_token='admin_token',
                confirmed_at=datetime.datetime.now(),
                roles=['admin']
            )
        if not security.user_datastore.find_user(email='dev@test.com'):
            security.user_datastore.create_user(
                email='dev@test.com',
                password=hash_password('test'),
                auth_token='dev_token',
                confirmed_at=datetime.datetime.now(),
                roles=['developer']
            )
        if not security.user_datastore.find_user(email='sym@test.com'):
            security.user_datastore.create_user(
                email='sym@test.com',
                password=hash_password('test'),
                auth_token='sym_token',
                confirmed_at=datetime.datetime.now(),
                roles=['sym_uploader']
            )
    except Exception as e:
        print(e)
