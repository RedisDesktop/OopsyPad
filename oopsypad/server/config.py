import os
import subprocess
from raven.versioning import fetch_git_sha

DEV, TEST, PROD = 'dev', 'test', 'prod'

DB_NAMES = {
    DEV: 'oopsy_pad_dev',
    TEST: 'oopsy_pad_test',
    PROD: 'oopsy_pad'
}


class Config:
    SECRET_KEY = 'dev'

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    CELERY_BROKER_URL = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

    ROOT_DIR = subprocess.check_output(
        ['git', 'rev-parse', '--show-toplevel']).rstrip().decode()
    DUMPS_DIR = os.path.join(ROOT_DIR, 'dumps')
    SYMFILES_DIR = os.path.join(ROOT_DIR, 'symbols')

    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    SECURITY_PASSWORD_SALT = SECRET_KEY
    SECURITY_UNAUTHORIZED_VIEW = None
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_USER_TEMPLATE = 'security/login.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'security/register.html'

    ENABLE_SENTRY = False
    SENTRY_DSN = ''
    SENTRY_CONFIG = {
        'release': fetch_git_sha(ROOT_DIR),
    }


class DevConfig(Config):
    DEBUG = True
    MONGODB_SETTINGS = {'DB': DB_NAMES[DEV]}


class TestConfig(Config):
    DEBUG = False
    TESTING = True

    MONGODB_SETTINGS = {'DB': DB_NAMES[TEST]}
    LIVESERVER_PORT = 8000


class ProdConfig(Config):
    DEBUG = False
    MONGODB_SETTINGS = {'DB': DB_NAMES[PROD]}

    ENABLE_SENTRY = True


app_config = {
    DEV: DevConfig,
    TEST: TestConfig,
    PROD: ProdConfig
}
