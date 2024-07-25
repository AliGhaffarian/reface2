#learn logging
#pyroute2
import pyroute2
import pathlib
import argparse
import logging

logger = logging.getLogger("reface2")
logging.basicConfig()
logger.level = logging.INFO

iproute = pyroute2.IPRoute()

from libnmap.parser import *
from libnmap.process import NmapProcess
from time import sleep
conf = {'nmap-options' : '-sn'} 
conf.update({'verbose' : True, 'debug' : False})




def decide_target():
    pass
def decide_network():
    pass
def decide_effected_device():
    pass

def become_host(interface_name, ip_address, netmask, mac, ttl = 64):
    change_mac(interface_name, mac)
    change_ip(interface_name, ip_address)
    if ttl != 64:
        change_os_ttl(ttl)

def get_my_link(interface_name):
    links = iproute.get_links()
    for link in links:
        if link['attrs'][0][1] == interface_name:
            return link

def change_mac(interface_name, new_mac):
    mylink = get_my_link(interface_name)
    
    current_mac = ""
    perm_mac = ""
    obtained_cred = 0
    for attr in mylink['attrs']:
        if attr[0] == 'IFLA_ADDRESS':
            current_mac = attr[1]
            obtained_cred += 1
            
        if attr[0] == 'IFLA_PERM_ADDRESS':
            perm_mac = attr[1]
            obtained_cred += 1
    
        if obtained_cred == 2:
            break
    
    

    logger.info(f"current mac: {current_mac}")
    logger.info(f"perm mac: {perm_mac}")



    pass
def change_ip(ip_address, netmask, interface_name):
    pass

def nmap_scan(network):
    nmap = NmapProcess(network, conf['nmap-options'])
    nmap.sudo_run_background()
    last_task = nmap.current_task
    last_progress = nmap.progress
    
    while nmap.is_running():
        if(last_progress != nmap.progress):
            last_progress = nmap.progress
            last_task = nmap.current_task
            logger.info(last_task.name)
            logger.info(last_progress)
        sleep(2) 
    return NmapParser.parse_fromstring(nmap.stdout)


def filter_hosts(condition, hosts):
    condition_compiled = compile(condition, '', 'eval')
    result =[] 
    for host in hosts:
        if(eval(condition_compiled)):
            result.append(host)
    return result


def handle_args():
    pass


def main():
    change_mac('eth0', "")
    
if __name__ == "__main__":
    main()
