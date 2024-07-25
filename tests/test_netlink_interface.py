import pyroute2
import logging
import os
import colorlog
import sys
import string
import random
import time
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

config = {
        "allowed_interfaces_to_manipulate" : ["wlan0"],
        "poll_timeout" : 1,
        "interface_change_state_sleep" : 2
        }

IPR = pyroute2.IPRoute()

def list_interface_names():
    result = []
    for interface in IPR.get_links():
        result.append(interface.get_attr("IFLA_IFNAME"))
    return result

def test_interface_exists():
    interface_names = list_interface_names()
    logger.debug(f"testing with interface list {interface_names=}")
    
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
        logger.debug(f"[+] passed on {name=}, expected to be True")

    for name in invalid_interface_names:
        assert netlink_interface.interface_exists(name) == False
        logger.debug("[+] passed on {name=}, expected to be False")

    logger.info("[+] interface_exists passed")

def dump_info_for(interface_name):
    interface_info, = IPR.link('dump', ifname=interface_name)
    if interface_info is None:
        logger.debug(f"dumping for {interface_name=} failed... polling")
        interface_info, = IPR.poll(IPR.link, 'dump', timeout=config['poll_timeout'], ifname=interface_name)
        
        if interface_info is None:
            logger.error(f"can't dump info for {interface_name=}")
    return interface_info

def test_update_interface_state():
    def flip_state_of_all_interfaces():
        for interface in interfaces:
            interface_info = dump_info_for(interface)

            if interface_info is None:
                pass

            elif interface_info['state'] == 'up':
                netlink_interface.update_interface_state(interface, 'down')
                time.sleep(config["interface_change_state_sleep"])
                assert dump_info_for(interface)['state'] == 'down'

            elif interface_info['state'] == 'down':
                netlink_interface.update_interface_state(interface, 'up')
                time.sleep(config["interface_change_state_sleep"])
                assert dump_info_for(interface)['state'] == 'up'

            else:
                logger.critical(f"un expected event!!! {interface_info['state']=}")

    
    interfaces = []

    if len(config["allowed_interfaces_to_manipulate"]) == 0:
        raise NotImplemented
    else:
        interfaces = config["allowed_interfaces_to_manipulate"]
        
    flip_state_of_all_interfaces()
    flip_state_of_all_interfaces()
    
    logger.info(f"[+] update_interface_state passed")



if __name__ == "__main__":
    test_interface_exists()
    test_update_interface_state()

