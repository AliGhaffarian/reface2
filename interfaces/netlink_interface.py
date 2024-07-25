"""
the netlink interface to the main_interface
"""


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
stdout_handler.setLevel(logging.INFO)

logger.addHandler(stdout_handler)
#---end of logger setup---


config = {'dump_timeout': 5}

IPR = pyroute2.IPRoute()


#make room->valid_link_states = ['up', 'down']

def update_interface_dump():
    global interfaces
    interfaces = IPR.get_links()

def update_interface_state(interface_name, state):
    """
    change the state an interface by name
    state can be either "up" or "down"
    example:
        update_dev_state("wlan0", "up")
    """
    #ensure the state is changed otherwise return err num and log 
    #handle timeout

    (peer,) = IPR.poll(IPR.link, 'dump', timeout=config['dump_timeout'], ifname=interface_name)
    IPR.link('set', index=peer['index'], state=state)

def interface_exists(interface_name):
    interfaces = IPR.get_links()
    for interface in interfaces:
        if interface.get_attr('IFLA_IFNAME') == interface_name:
            logger.debug(f"{dev_name=} exists")
            return True
    logger.debug(f"{dev_name=} doesn't exist")
    return False

