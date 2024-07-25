import logging
import logging.config
import colorlog
import sys
"""
a simple wrapper for logging for simpler logger setups in the scritps
"""

# Define the format and log colors
log_format = '%(asctime)s [%(levelname)s] %(name)s [%(funcName)s]: %(message)s'
log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
        }

# Create the ColoredFormatter object
console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s' + log_format,
        log_colors = log_colors
        )

