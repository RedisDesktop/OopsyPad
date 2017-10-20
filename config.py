MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB (max size of rdm sym file ever seen is 1.9 MB)

CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

SYMFILES_DIR = 'symbols'

MONGODB_SETTINGS = {'DB': "oopsy_pad"}
