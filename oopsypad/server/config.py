import os

DEV, TEST, PROD = 'dev', 'test', 'prod'

DB_NAMES = {
    DEV: 'oopsy_pad_dev',
    TEST: 'oopsy_pad_test',
    PROD: 'oopsy_pad'
}

mongo_host = os.environ.get('MONGODB_HOST', 'localhost')

class Config:
    SECRET_KEY = 'dev'

    CREATE_TEST_USERS = False

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

    BIN_DIR = os.path.join(ROOT_DIR, 'bin')
    # 3rd party binaries
    DUMP_SYMS = os.path.join(BIN_DIR, 'dump_syms')
    MINIDUMP_STACKWALK = os.path.join(BIN_DIR, 'minidump_stackwalk')
    STACKWALKER = os.path.join(BIN_DIR, 'stackwalker')

    DUMPS_DIR = os.path.join(ROOT_DIR, 'dumps')
    SYMFILES_DIR = os.path.join(ROOT_DIR, 'symbols')

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    SECURITY_PASSWORD_HASH = 'sha512_crypt'
    SECURITY_PASSWORD_SALT = SECRET_KEY
    SECURITY_UNAUTHORIZED_VIEW = None
    SECURITY_REGISTERABLE = True
    SECURITY_REGISTER_URL = '/register'
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_USER_TEMPLATE = 'security/login.html'
    SECURITY_REGISTER_USER_TEMPLATE = 'security/register.html'

    SETUP_ADMIN_URL = '/setup-admin'

    ENABLE_SENTRY = False
    SENTRY_DSN = ''

class DevConfig(Config):
    DEBUG = True
    CREATE_TEST_USERS = True

    MONGODB_SETTINGS = {
        'DB': DB_NAMES[DEV],
        'HOST': mongo_host
    }


class TestConfig(Config):
    DEBUG = False
    TESTING = True
    CREATE_TEST_USERS = True

    MONGODB_SETTINGS = {
        'DB': DB_NAMES[TEST],
        'HOST': mongo_host
    }

    LIVESERVER_PORT = 8000


class ProdConfig(Config):
    DEBUG = False

    MONGODB_SETTINGS = {
        'DB': DB_NAMES[PROD],
        'HOST': mongo_host
    }

    ENABLE_SENTRY = True


app_config = {
    DEV: DevConfig,
    TEST: TestConfig,
    PROD: ProdConfig
}
