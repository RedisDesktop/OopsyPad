import os
import subprocess

DEV, TEST, PROD = 'dev', 'test', 'prod'

DB_NAMES = {
    DEV: 'oopsy_pad_dev',
    TEST: 'oopsy_pad_test',
    PROD: 'oopsy_pad'
}


class Config:
    SECRET_KEY = os.urandom(24)

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    CELERY_BROKER_URL = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

    ROOT_DIR = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).rstrip().decode()
    DUMPS_DIR = os.path.join(ROOT_DIR, 'dumps')
    SYMFILES_DIR = os.path.join(ROOT_DIR, 'symbols')


class DevConfig(Config):
    DEBUG = True
    MONGODB_SETTINGS = {'DB': DB_NAMES[DEV]}


class TestConfig(Config):
    DEBUG = False
    TESTING = True

    MONGODB_SETTINGS = {'DB': DB_NAMES[TEST]}


class ProdConfig(Config):
    DEBUG = False
    MONGODB_SETTINGS = {'DB': DB_NAMES[PROD]}


app_config = {
    DEV: DevConfig,
    TEST: TestConfig,
    PROD: ProdConfig
}
