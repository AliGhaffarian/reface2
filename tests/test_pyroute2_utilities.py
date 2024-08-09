import pyroute2
import logging
import os
import colorlog
import sys
import string
import random
import time
import scapy.all


sys.path.insert(0, os.path.abspath('../..'))
#../logging_utilities/config.py
import reface2.utilities.logging_utilities.config as config
import reface2.utilities.pyroute2_utilities as pyroute2_utilities
import reface2.utilities.constants.linux_errors as linux_errors
import reface2.utilities.constants.mac_templates as mac_templates
#---logger setup---
FILENAME = os.path.basename(__file__).split('.')[0]
logger = logging.getLogger(FILENAME)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(config.console_formatter)
stdout_handler.setLevel(logging.INFO)

logger.addHandler(stdout_handler)
#---end of logger setup---


INTERFACES_TO_MANIPULATE = "interfaces_to_manipulate"
def make_invalid_interface(count):
    name_size=7
    chars = string.ascii_letters + string.digits
    interface_list = pyroute2_utilities.interface_list()
    result = []

    i=0
    while ( i < count ):
        interface_name = ''.join(random.choice(chars) for _ in range(name_size))
        if interface_name not in interface_list:
            i += 1
            result.append(interface_name)

    return result

INVALID_INTERFACE_LIST = make_invalid_interface(5)

TIMEOUT = "timeout"
INTERFACE_CHANGE_STATE_SLEEP = "interface_change_state_sleep"
conf = {
        INTERFACES_TO_MANIPULATE : ["wlan0"],
        TIMEOUT : 1,
        INTERFACE_CHANGE_STATE_SLEEP : 2
        }

ipr = pyroute2.IPRoute()

#list of valid interfaces to manipulate
#if no allowed interfaces are listed a virtual interface is created
interfaces_to_manipulate = []
if len(conf[INTERFACES_TO_MANIPULATE]) == 0:
    raise NotImplementedError
else:
    interfaces_to_manipulate = conf[INTERFACES_TO_MANIPULATE]
  
logger.info(f"[*] interfaces to test on: {interfaces_to_manipulate}")

def new_mac_for_interface(interface_name):
    """
    a valid mac address thats not the current mac address of the interface
    gotta make a randmac with vendor specification
    """
    if_dump = ipr.poll(ipr.link, "dump", ifname = interface_name, timeout=conf[TIMEOUT])[0]
    current_mac = if_dump.get_attr("IFLA_ADDRESS")
    random_mac = str(
            scapy.all.RandMAC(
                mac_templates.random_mac_template()
                )
            )

    while ( random_mac == current_mac ):
        random_mac = str(
                scapy.all.RandMAC(
                    mac_templates.random_mac_template()
                    )
                )

    return random_mac


def test_change_mac():
    #try to change mac of interface
    for interface in interfaces_to_manipulate:
        test_mac = new_mac_for_interface(interface)
        interface_state = ipr.poll(ipr.link, "dump", ifname = interface ,timeout=conf[TIMEOUT])[0]\
                ['state']
        logger.debug(f"{interface} is expected to be {interface_state} after changing the mac")

        errno = pyroute2_utilities.change_mac(interface, test_mac)
        if errno:
            logger.warning(f"[-] unexpected error on change mac {linux_errors.error_to_string[errno]}")

        interdump = ipr.poll(ipr.link, "dump", ifname = interface)[0]
        logger.debug(f"dump of {interface=} after changing the mac: {interdump}")
        #theres the possibility of errno being non-zero thats if shutting down the interface fails
        assert interdump['state'] == interface_state
        assert interdump.get_attr("IFLA_ADDRESS") == test_mac

    #try to change mac of non existent interface
    for interface in INVALID_INTERFACE_LIST:
        test_mac = str(
                scapy.all.RandMAC(
                    mac_templates.random_mac_template()
                    )
                )

        errno = pyroute2_utilities.change_mac(interface, test_mac)
        assert errno == linux_errors.ENODEV
    
    #try to change mac of interface to current interface
    for interface in interfaces_to_manipulate:
        interface_mac = ipr.poll(ipr.link, "dump", ifname=interface)[0].get_attr("IFLA_ADDRESS")
        errno = pyroute2_utilities.change_mac(interface, interface_mac)
        assert errno == 0
    logger.info("[+] passed")


if __name__ == "__main__":
    stdout_handler.setLevel("DEBUG")
    pyroute2_utilities.stdout_handler.setLevel("DEBUG")
    test_change_mac()
