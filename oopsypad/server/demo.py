import datetime

from flask_security.utils import hash_password

from oopsypad.server import security

ADMIN_TOKEN = 'admin_token'
ADMIN_EMAIL = 'admin@test.com'

DEV_TOKEN = 'dev_token'
DEV_EMAIL = 'dev@test.com'

SYM_TOKEN = 'sym_token'
SYM_EMAIL = 'sym@test.com'

PSW = 'test'


def create_test_users():
    try:
        if not security.user_datastore.find_user(email=ADMIN_EMAIL):
            security.user_datastore.create_user(
                email=ADMIN_EMAIL,
                password=hash_password(PSW),
                auth_token=ADMIN_TOKEN,
                confirmed_at=datetime.datetime.now(),
                roles=['admin']
            )
        if not security.user_datastore.find_user(email=DEV_EMAIL):
            security.user_datastore.create_user(
                email=DEV_EMAIL,
                password=hash_password(PSW),
                auth_token=DEV_TOKEN,
                confirmed_at=datetime.datetime.now(),
                roles=['developer']
            )
        if not security.user_datastore.find_user(email=SYM_EMAIL):
            security.user_datastore.create_user(
                email=SYM_EMAIL,
                password=hash_password(PSW),
                auth_token=SYM_TOKEN,
                confirmed_at=datetime.datetime.now(),
                roles=['sym_uploader']
            )
    except Exception as e:
        print(e)
