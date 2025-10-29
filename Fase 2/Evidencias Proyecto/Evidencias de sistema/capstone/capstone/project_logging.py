# project_logging.py
import logging
import sys

class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarillo
        'ERROR': '\033[31m',    # Rojo
        'CRITICAL': '\033[41m', # Fondo rojo
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'colored': {
            '()': ColorFormatter,
            'format': '[{levelname}] {asctime} [{name}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
            'stream': sys.stdout,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
