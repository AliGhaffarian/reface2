import logging
import logging.config
import colorlog


format = '%(asctime)s [%(levelname)s] %(name)s [%(funcName)s]: %(message)s'
def easy_get_logger(name, str_level, most_verbose_level = "DEBUG"):
    logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    '()': 'colorlog.ColoredFormatter',
                    'format': "%(log_color)s" + format,
                    'log_colors': {
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red',
                        },
                    },
                },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'level': str_level,
                    },
                },
            'loggers': {
                name : {
                    'handlers': ['console'],
                    'level': most_verbose_level,
                    'propagate': False
                    },
                }
            }

    logging.config.dictConfig(logging_config)
    return logging.getLogger(name)

def easy_file_handler(filename, int_loglevel):
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(int_loglevel)
    file_handler.setFormatter(logging.Formatter(format))
    return file_handler


