import pyroute2
import logging
import os
import colorlog
import sys
import string
import random
import time
import scapy.all
import errno
import pytest
import ipaddress
from functools import wraps
import itertools

sys.path.insert(0, os.path.abspath('../..'))
#../logging_utilities/config.py
import reface2.utilities.logging_utilities.config as config
import reface2.utilities.pyroute2_utilities as pyroute2_utilities
import reface2.utilities.constants.mac_templates as mac_templates
#---logger setup---
FILENAME = os.path.basename(__file__).split('.')[0]
logger = logging.getLogger(FILENAME)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(config.console_formatter)
stdout_handler.setLevel(logging.DEBUG)

logger.addHandler(stdout_handler)
#---end of logger setup---

ipr = pyroute2.IPRoute()


conf = {
        'INTERFACES_TO_MANIPULATE' : ["wlan0"],
        'TIMEOUT' : 2,
        'INTERFACE_CHANGE_STATE_SLEEP' : 2,
        'PARAMS_LENGTH' : 2,
        'ANY_ERRORNO' :1,
        'RANDOM_INTERFACE_NAME_SIZE' : 7
        }




#list of valid interfaces to manipulate
#if no allowed interfaces are listed a virtual interface is created
interfaces_to_manipulate = []
if len(conf['INTERFACES_TO_MANIPULATE']) == 0:
    raise NotImplementedError
else:
    interfaces_to_manipulate = conf['INTERFACES_TO_MANIPULATE']
  
logger.info(f"[*] interfaces to test on: {interfaces_to_manipulate}")



def make_invalid_interface(count):
    global conf
    name_size=conf['RANDOM_INTERFACE_NAME_SIZE']

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

INVALID_INTERFACE_LIST = make_invalid_interface(conf['PARAMS_LENGTH'])

INVALID_IFNAME_LIST = []
for ifname in make_invalid_interface(conf['PARAMS_LENGTH']):
    INVALID_IFNAME_LIST.append((ifname, errno.ENODEV))

VALID_IFNAME_LIST = []
for ifname in interfaces_to_manipulate:
    VALID_IFNAME_LIST.append((ifname, 0))

TTL_BITS = 8
IPV4_BITS = 32
IPV6_BITS = 128

INVALID_TTL_LIST = []
INVALID_TTL_LIST += [(random.choice(range(-255, 0)), conf['ANY_ERRORNO']) for i in range (int (conf['PARAMS_LENGTH'] / 2))]
INVALID_TTL_LIST += [(random.choice(range(256, 10000)), conf['ANY_ERRORNO']) for i in range (int(conf['PARAMS_LENGTH'] / 2))]
VALID_TTL_LIST = [(random.choice(range(0, 2**TTL_BITS - 1)), 0) for i in range (conf['PARAMS_LENGTH'])]



#for some reason pyroute 2 raises an string as errno
INVALID_MTU_ERR_MSG = "argument out of range"
INVALID_MTU_LIST = [
        (random.choice(range(-255, 0)), INVALID_MTU_ERR_MSG)
         for i in range (conf['PARAMS_LENGTH'])]
VALID_MTU_LIST = [
        (random.choice(range(1400, 1500)), 0) 
        for i in range (conf['PARAMS_LENGTH'])]


INVALID_MAC_LIST = []
INVALID_MAC_LIST.append(("FF:FF:FF:FF:FF:FF", errno.EADDRNOTAVAIL))
INVALID_MAC_LIST.append(("00:00:00:00:00:00", errno.EADDRNOTAVAIL))

INVALID_UBYTE_RANGE_ERR_MSG = "ubyte format requires 0 <= number <= 255"
INVALID_IPV4_NETMASK_LIST = [
        (random.choice(range(IPV4_BITS + 1, IPV4_BITS + 50)), errno.EINVAL)
        for i in range(int(conf['PARAMS_LENGTH'] / 2))
        ]


INVALID_IPV4_NETMASK_LIST += [
        (random.choice(range(-100, 0)), INVALID_UBYTE_RANGE_ERR_MSG)
        for i in range(int(conf['PARAMS_LENGTH'] / 2))
        ]

VALID_IPV4_NETMASK_LIST = [
        (random.choice(range(0, IPV4_BITS)), 0)
        for i in range(conf['PARAMS_LENGTH'])
        ]
        


#array of (random_mac, 0)
VALID_MAC_LIST = [(str(
                    scapy.all.RandMAC(
                        mac_templates.random_mac_template()
                        )
                    ), 0)
                  for i in range (conf['PARAMS_LENGTH'])]


VALID_IPV4_LIST = [
        ( ipaddress.IPv4Address(random.choice(range(2**IPV4_BITS - 1))), 0 )
                 for i in range(conf['PARAMS_LENGTH'])
                 ]


params = {
        "ifname" : INVALID_IFNAME_LIST + VALID_IFNAME_LIST,
        "ttl" : INVALID_TTL_LIST + VALID_TTL_LIST,
        "mac" : INVALID_MAC_LIST + VALID_MAC_LIST,
        "ip" : VALID_IPV4_LIST ,
        "ipv4_net_mask" : INVALID_IPV4_NETMASK_LIST + VALID_IPV4_NETMASK_LIST,
        "mtu" : VALID_MTU_LIST + INVALID_MTU_LIST
        }

logger.debug(f"{params=}")
def new_mac_for_interface(interface_name):
    """
    a valid mac address thats not the current mac address of the interface
    gotta make a randmac with vendor specification
    """
    if_dump = ipr.poll(ipr.link, "dump", ifname = interface_name, timeout=conf['TIMEOUT'])[0]
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


def generate_pytest_params(*arrays):
    """
    Generates test parameter combinations.

    Takes arrays of 2-entry tuples and returns an array of tuples with combinations
    of the first entry from each input array and a union of the second entries.

    Parameters:
    *arrays : one or more lists of 2-entry tuples.

    Returns:
    List of tuples containing combinations of the first entries and a list of second entries.
    """
    combined = []
    for combination in itertools.product(*arrays):
        first_entries = tuple([t[0] for t in combination])
        second_entries = [t[1] for t in combination]
        second_entries = list(dict.fromkeys(second_entries))
        if 0 in second_entries:
            second_entries.remove(0)
        iter_result = first_entries + ((second_entries,))
        combined.append(iter_result)
    return combined

@pytest.mark.parametrize("ifname, mac, expected_exception_codes", generate_pytest_params(params['ifname'], params['mac']))
def test_change_mac(ifname, mac, expected_exception_codes):
    #this prevents these two to be equal accidentally
    last_mac = ""
    current_mac = "A"
    logger.debug(f"called with {ifname=}, {mac=}, {expected_exception_codes=}")
    
    is_ifname_valid = ifname in [ifname_tuple[0] for ifname_tuple in VALID_IFNAME_LIST]

    if is_ifname_valid:
        last_mac = ipr.poll(ipr.link, "dump", ifname=ifname, timeout=conf['TIMEOUT'])[0].get_attr("IFLA_ADDRESS")
    try:
        pyroute2_utilities.change_mac(ifname, mac)

    except Exception as e:

        if is_ifname_valid:
            current_mac = ipr.poll(ipr.link, "dump", ifname=ifname, timeout=conf['TIMEOUT'])[0].get_attr("IFLA_ADDRESS")
            assert current_mac == last_mac
        assert e.args[0] in expected_exception_codes, str(e) + " " + str(ifname)
        return
    
    current_mac = ipr.poll(ipr.link, "dump", ifname=ifname, timeout=conf['TIMEOUT'])[0].get_attr("IFLA_ADDRESS")
    assert current_mac == mac
    assert len(expected_exception_codes) == 0
        
@pytest.mark.parametrize("ifname, ip, mac, netmask, ttl, mtu, expected_exception_codes", generate_pytest_params(params['ifname'], params['ip'], params['mac'], params['ipv4_net_mask'], params['ttl'], params['mtu']))
def test_set_host_data(ifname, ip, mac, netmask, ttl, mtu, expected_exception_codes):
    logger.debug(f"called with {ifname=}, {ip=}, {mac=}, {ttl=}, {mtu=}, {expected_exception_codes=}")
    

    is_ifname_valid = ifname in [ifname_tuple[0] for ifname_tuple in VALID_IFNAME_LIST]
    if is_ifname_valid:
        last_state = pyroute2_utilities.simple_interface_dump(ifname)
    try:
        pyroute2_utilities.set_host_data(ifname=ifname, mac=mac, ip=ip, netmask=netmask, ttl=ttl, mtu=mtu)
    except Exception as e:

        logger.debug(e)
        if is_ifname_valid:
            assert pyroute2_utilities.simple_interface_dump(ifname) == last_state

        assert e.args[0] in expected_exception_codes
        return

    assert len(expected_exception_codes) == 0

