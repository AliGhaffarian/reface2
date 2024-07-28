import pyroute2
import logging
import os
import colorlog
import sys
import string
import random
import time
import scapy.all


sys.path.insert(0, os.path.abspath('..'))
#../logging_utilities/config.py
import logging_utilities.config as config
import interfaces.netlink_interface as netlink_interface

import mac_templates
#---logger setup---
FILENAME = os.path.basename(__file__).split('.')[0]
logger = logging.getLogger(FILENAME)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(config.console_formatter)
stdout_handler.setLevel(logging.INFO)

logger.addHandler(stdout_handler)
#---end of logger setup---

config = {
        "allowed_interfaces_to_manipulate" : ["wlan0"],
        "poll_timeout" : 1,
        "interface_change_state_sleep" : 2
        }

IPR = pyroute2.IPRoute()

#list of valid interfaces to manipulate
#if no allowed interfaces are listed a virtual interface is created
interfaces_to_manipulate = []
if len(config["allowed_interfaces_to_manipulate"]) == 0:
    raise NotImplemented
else:
    interfaces_to_manipulate = config["allowed_interfaces_to_manipulate"]
  
logger.info(f"interfaces to test on: {interfaces_to_manipulate}")

