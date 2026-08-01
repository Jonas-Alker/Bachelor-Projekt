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
            'console': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout'
            },
            'file_handler_info': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/app.log',
                'maxBytes': 10000000,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'file_handler_debug': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/debug.log',
                'maxBytes': 10000000,
                'backupCount': 5,
                'encoding': 'utf-8',
            }
        },
    'loggers': {
        '': {
            'handlers': ['file_handler_info', 'file_handler_debug', 'console'],
            'level': 'DEBUG',
            'propagate': True,

        }
    }
}