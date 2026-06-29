import os
from os.path import exists

os.makedirs("logs", exist_ok=True)

LOGGING_SETUP = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        'standard': {
            'format': '%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        },
    },
    'handlers': {
            'file_handler': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/app.log',
                'maxBytes': 10000000,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
        },
    'loggers': {
        '': {
            'handlers': ['file_handler'],
            'level': 'DEBUG',
            'propagate': True,

        }
    }
}