import pyroute2
import logging
import os
import colorlog
import sys
import string
import random
sys.path.insert(0, os.path.abspath('..'))
#../logging_utilities/config.py
import logging_utilities.config as config
import interfaces.netlink_interface as netlink_interface

#---logger setup---
FILENAME = os.path.basename(__file__).split('.')[0]
logger = logging.getLogger(FILENAME)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(config.console_formatter)
stdout_handler.setLevel(logging.INFO)

logger.addHandler(stdout_handler)
#---end of logger setup---

IPR = pyroute2.IPRoute()

def list_interface_names():
    result = []
    for interface in IPR.get_links():
        result.append(interface.get_attr("IFLA_IFNAME"))
    return result

def interface_exists():
    interface_names = list_interface_names()
    
    #making invalid interface names
    invalid_interface_names = []
    i = 0
    while(i < 5):
        random_string = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        if (random_string not in interface_names) and\
                (random_string not in invalid_interface_names):
                    invalid_interface_names.append(random_string)
                    i += 1
    
    for name in interface_names:
        assert netlink_interface.interface_exists(name) == True

    for name in invalid_interface_names:
        assert netlink_interface.interface_exists(name) == False

    logger.info("[+] interface_exists passed")


interface_exists()
