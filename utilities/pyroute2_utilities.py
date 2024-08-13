import pyroute2
import logging
import os
import sys
sys.path.insert(0, os.path.abspath("../../"))
import errno

import reface2.utilities.logging_utilities.config as config


FILENAME = os.path.basename(__file__).split('.')[0]

logger = logging.getLogger(FILENAME)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(config.console_formatter)
stdout_handler.setLevel(logging.INFO)

logger.addHandler(stdout_handler)
#---end of logger setup---

TIMEOUT="timeout"
conf = {
        TIMEOUT : 2,
        }


ipr = pyroute2.IPRoute()

def interface_list():
    result=[]
    for info in ipr.poll(ipr.link, "dump"):
        dump=info[0]
        result.append(dump.get_attrs("IFLA_IFNAME")[0])
    logger.debug(f"list of interfaces: {result=}")
    return result

def change_mac(interface_name : str, new_mac : str)->bool:
    
    if interface_name not in interface_list():
        raise Exception(errno.ENODEV, os.strerror(errno.ENODEV))

    mylink = ipr.poll(ipr.link, "dump", ifname=interface_name, timeout=conf[TIMEOUT])[0]
    logger.debug(f"dumped info for interface {interface_name=}")

    current_mac = ""
    perm_mac = ""
    obtained_cred = 0
    for attr in mylink['attrs']:
        if attr[0] == 'IFLA_ADDRESS':
            current_mac = attr[1]
            logger.debug(f"current mac of {interface_name}: {current_mac=}")
            if new_mac == current_mac :
                logger.info("current mac is new_mac no need to do anything")
                return 0
            obtained_cred += 1

        if obtained_cred == 1:
            break
 
    result = ""
    try:
        logger.debug(f"trying to set mac for {interface_name=}, {new_mac=}")
        result = ipr.poll(ipr.link, "set", ifname=interface_name, address=new_mac, timeout =conf[TIMEOUT])[0]
        logger.debug(f"result of set mac {result}")
    except pyroute2.NetlinkError as e:
        if e.code != errno.EBUSY:
            raise e

        logger.info(f"{interface_name} is busy shutting down the interface")

        temp_result = ipr.poll(ipr.link, "set", ifname=interface_name, state="down", timeout=conf[TIMEOUT])[0]

        if temp_result['error']:
            raise Exception(temp_result['error'], os.strerror(temp_result['error']))

        logger.debug(f"result of shutting down the interface: {temp_result}")

        result = ipr.poll(ipr.link, "set", ifname=interface_name, address=new_mac, timeout =conf[TIMEOUT])[0]
        logger.debug(f"result of set mac : {result}")
        
        temp_result = ipr.poll(ipr.link, "set", ifname=interface_name, state="up", timeout=conf[TIMEOUT])[0]
        logger.debug(f"result of starting up the interface: {temp_result}")
    except Exception as e:
        raise e
    
    #return error code, usually 0
    return result['error']


def set_host_data(ifname, ip, mac, ip_netmask=32, ttl=None):
    """
    adds ip address and sets mac address on the interface
    """
    try:
        ipr.addr("add", index=ipr.link_lookup(ifname=ifname)[0], address=ip, prefixlen=ip_netmask)
    except Exception as e:
        if e.code != EEXIST:
            raise e
    change_mac(ifname, mac)

def switch_to_ip(ifname, ip, netmask):
    #check all routes for ifname
    #1_delete routes for networks with <= netmask
    #2_add a route to the target network with prefered ip of {ip}
    #3_if the network was default gateway set a default gateway too
    #what about other interfaces with the same network dest?
        #if we got a prefered src to that network we should be good if the other interfaces are shutdown
    raise NotImplementedError
