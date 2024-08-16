import pyroute2
import logging
import os
import sys
import socket
sys.path.insert(0, os.path.abspath("../../"))
import errno

import reface2.utilities.logging_utilities.config as config
import reface2.utilities.shell_utilities as shell_utilities
import reface2.utilities.constants.sysctl_params as sysctl_params


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

def interface_list()->list:
    result=[]
    for info in ipr.poll(ipr.link, "dump"):
        dump=info[0]
        result.append(dump.get_attrs("IFLA_IFNAME")[0])
    logger.debug(f"list of interfaces: {result=}")
    return result

def change_mac(interface_name : str, new_mac : str)->bool:
    
    if interface_name not in interface_list():
        raise Exception(errno.ENODEV, os.strerror(errno.ENODEV))

    
    result = ""
    try:
        logger.debug(f"trying to set mac for {interface_name=}, {new_mac=}")
        result = ipr.poll(ipr.link, "set", ifname=interface_name, address=new_mac, timeout =conf[TIMEOUT])[0]
        logger.debug(f"result of set mac {result}")
    except pyroute2.NetlinkError as e:
        if e.args[0] != errno.EBUSY:
            raise e

        logger.info(f"{interface_name} is busy shutting down the interface")

        temp_result = ipr.poll(ipr.link, "set", ifname=interface_name, state="down", timeout=conf[TIMEOUT])[0]

        if temp_result['error']:
            raise Exception(temp_result['error'], os.strerror(temp_result['error']))

        logger.debug(f"result of shutting down the interface: {temp_result}")

        result = ipr.poll(ipr.link, "set", ifname=interface_name, address=new_mac, timeout =conf[TIMEOUT])[0]
        logger.debug(f"result of set mac : {result}")
        
        logger.info(f"starting up {interface_name}")
        temp_result = ipr.poll(ipr.link, "set", ifname=interface_name, state="up", timeout=conf[TIMEOUT])[0]
        
        assert temp_result['error'] == 0
        
        logger.debug(f"result of starting up the interface: {temp_result}")
    except Exception as e:
        raise e
    
    #if this is not 0 i did something wrong
    assert result['error'] == 0
    return 0


def simple_interface_dump(ifname)->dict:
    """
    return:
    {
    "ipv4" : [] # array of "{ipv4}/{netmask}"
    "ipv6" : [] # array of "{ipv6}/{netmask}"
    "mac" : "" # mac
    "mtu" : int # mtu
    "ttl" : int # ttl
    "state", str #interface state
    }
    """
    simple_dump = {}
    ipv4s = []
    ipv6s = []
            
    for addr_dump in ipr.addr("dump", index=ipr.link_lookup(ifname=ifname)[0]):
        if addr_dump['family'] == socket.AF_INET:
            temp_ipv4 = addr_dump.get_attr("IFA_ADDRESS") + "/" + str(addr_dump['prefixlen'])
            ipv4s.append(temp_ipv4)
        if addr_dump['family'] == socket.AF_INET6:
            temp_ipv6 = addr_dump.get_attr("IFA_ADDRESS") + "/" + str(addr_dump['prefixlen'])
            ipv6s.append(temp_ipv6)
                        
    link_dump = ipr.poll(ipr.link, "dump", ifname=ifname)[0]
    mac = link_dump.get_attr("IFLA_ADDRESS")
    mtu = link_dump.get_attr("IFLA_MTU")
    state = link_dump['state']
    ttl = shell_utilities.get_sysctl_param(sysctl_params.IPV4_DEFAULT_TTL)
 

    simple_dump.update({"ipv4" : ipv4s})
    simple_dump.update({"ipv6" : ipv6s})
    simple_dump.update({"mac" : mac})
    simple_dump.update({"mtu" : mtu})
    simple_dump.update({"ttl" : ttl})
    simple_dump.update({"state" : state})



    logger.debug(f"simple dump of {simple_dump=}")
    return simple_dump

def roll_back_interface_to_state(ifname : str, target_interface_state : dict)->bool:
    """
    sets interface attributes to the given simple dump
    simple dump is expected to provide the attributes the same way as simple_interface_dump() does
    """
    current_state = simple_interface_dump(ifname)
    
    if current_state['mac'] != target_interface_state['mac']:
        change_mac(ifname, target_interface_state['mac'])

    if current_state['ttl'] != target_interface_state['ttl']:
        shell_utilities.set_sysctl_param(sysctl_params.IPV4_DEFAULT_TTL, target_interface_state['ttl'])

    if current_state['mtu'] != target_interface_state['mtu']:
        ipr.poll(ipr.link, "set", ifname=ifname, mtu=target_interface_state['mtu'])


    #if ip address is not included in target interface state, delete it 
    for ip in current_state['ipv4']:
        if ip not in target_interface_state['ipv4']:
            ipr.poll(ipr.addr, "delete", index = ipr.link_lookup(ifname=ifname)[0], addr=ip.split("/")[0],\
                    prefixlen = ip.split("/")[1], family = socket.AF_INET)

    for ip in current_state['ipv6']:
        if ip not in target_interface_state['ipv6']:
            ipr.poll(ipr.addr, "delete", index = ipr.link_lookup(ifname=ifname)[0], addr=ip.split("/")[0],\
                    prefixlen = ip.split("/")[1], family = socket.AF_INET6)
 
    for ip in target_interface_state['ipv4']:
        if ip not in current_state['ipv4']:
            ipr.poll(ipr.addr, "add", index = ipr.link_lookup(ifname=ifname)[0], addr = ip.split("/")[0],\
                    prefixlen = ip.split("/")[1], family = socket.AF_INET)
            

    for ip in target_interface_state['ipv6']:
        if ip not in current_state['ipv6']:
            ipr.poll(ipr.addr, "add", index = ipr.link_lookup(ifname=ifname)[0], addr = ip.split("/")[0],\
                    prefixlen = ip.split("/")[1], family = socket.AF_INET6)
            
    if current_state['state'] != target_interface_state['state']:
        ipr.poll(ipr.link, "set", ifname=ifname, state = target_interface_state['state'])

def set_host_data(ifname, ip, mac, netmask=32, ttl=None, mtu=None)->bool:
    """
    adds ip address and sets mac address on the interface
    """
    
    if ifname not in interface_list():
        raise Exception(errno.ENODEV, os.strerror(errno.ENODEV))


    #get a backup of interface state
    last_interface_state = simple_interface_dump(ifname)
     
    if ttl is not None:
        err = shell_utilities.set_sysctl_param(sysctl_params.IPV4_DEFAULT_TTL, ttl)
        if err:
            roll_back_interface_to_state(ifname, last_interface_state)
            raise Exception(err, "error setting ttl")
            
    
    if mtu is not None:
        try:
            poll_info = ipr.poll(ipr.link, "set", index=ipr.link_lookup(ifname=ifname)[0], mtu=mtu)[0]
        except Exception as e:
            roll_back_interface_to_state(ifname, last_interface_state)
            raise e

    try:
        change_mac(ifname, mac)
    except Exception as e:
        roll_back_interface_to_state(ifname, last_interface_state)
        raise e


    try:
        poll_info = ipr.poll(ipr.addr, "add", index=ipr.link_lookup(ifname=ifname)[0], address=str(ip), prefixlen=netmask)[0]
    except Exception as e:
        if e.args[0] != errno.EEXIST:
            roll_back_interface_to_state(ifname, last_interface_state)
            raise e
        
    assert poll_info['error'] == 0
    return 0

def switch_to_ip(ifname, ip, netmask):
    #check all routes for ifname
    #1_delete routes for networks with <= netmask
    #2_add a route to the target network with prefered ip of {ip}
    #3_if the network was default gateway set a default gateway too
    #what about other interfaces with the same network dest?
        #if we got a prefered src to that network we should be good if the other interfaces are shutdown
    raise NotImplementedError
