import pyroute2
import logging
import os
import colorlog
import sys

sys.path.insert(0, os.path.abspath('..'))
#../logging_utilities/config.py
import logging_utilities.config as config

#---logger setup---
FILENAME = os.path.basename(__file__).split('.')[0]
logger = logging.getLogger(FILENAME)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(config.console_formatter)

logger.addHandler(stdout_handler)
#---end of logger setup---



