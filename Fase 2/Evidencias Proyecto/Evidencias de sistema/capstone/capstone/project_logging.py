# project_logging.py
import logging
import sys

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,  # Mantener loggers existentes
    'formatters': {
        'detailed': {
            'format': '[{levelname}] {asctime} [{name}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'stream': sys.stdout,
        },
    },
    'root': {  # Logger universal para todo el proyecto
        'handlers': ['console'],
        'level': 'DEBUG',  # Cambia a INFO o WARNING en producción
    },
}
