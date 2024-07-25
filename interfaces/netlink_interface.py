import pyroute2
import logging
import logging.config
import os
import colorlog

FILENAME = os.path.basename(__file__).split('.')[0]


#---setting up logger---
logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                '()': 'colorlog.ColoredFormatter',
                'format': '%(log_color)s%(asctime)s [%(levelname)s] %(name)s [%(funcName)s]: %(message)s',
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
                'level': 'DEBUG',
                },
            },
        'loggers': {
            FILENAME: {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False
                },
            }
        }

logging.config.dictConfig(logging_config)
logger = logging.getLogger(FILENAME)
#---end of logger setup---

