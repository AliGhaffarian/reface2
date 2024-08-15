import time
import pyroute2
import ipaddress
import reface_host
#constant keywords used to key into nmap report dictionaries
SCAN_METHOD_NMAP = "nmap"

SCAN_TYPE = "scan_type"
TIME = "time"
SCAN_INTERFACE_DUMP = "scan_interface_dump"
RAW_SCAN_DATA = "raw_scan_data"
HOSTS = "hosts"
STARRED_HOSTS = "starred_hosts"
COMMENT = "comment"
OTHER_DATA = "other_data"
PRIVILEGED = "privileged"


def make_reface_report_nmap(scan_name, interface_name = "", hosts = "", raw_scan_data = ""):
        return {
                scan_name : {
                    PRIVILEGD : 0 #bool
                    SCAN_TYPE : SCAN_METHOD_NMAP, #nmap parsed data
                    TIME : time.ctime(), #ctime
                    SCAN_INTERFACE_DUMP : "", #pyroute dump
                    RAW_SCAN_DATA :raw_scan_data, #nmap xml
                    HOSTS : hosts, #nmap parsed data
                    #from host.py
                    STARRED_HOSTS : [], #reface_host.reface_host
                    #comments are tuples of (comment, time.ctime())
                    COMMENT : [], #(string, ctime)
                    OTHER_DATA : {},
                    }
                }

def add_comment(report, comment):
    report[COMMENT].append((comment, time.ctime()))

def star_host(report, ipv4 = None, ipv6 = None, mac = None):
    host = find_host(report, ipv4, ipv6, mac)
    if host is None:
        logger.warning(f"{host} not found")
        return False
    host = reface_host.make_reface_host(host=host) 
    report[STARRED_HOSTS].append(host)
    return True

def find_starred_host(report, ipv4 = None, ipv6 = None, mac = None):
    condition_compiled = ""
    if ipv4 is not None:
        condition_compiled = compile(f"host.ipv4 == '{ipv4}'", '', 'eval')
    elif ipv6 is not None:
        condition_compiled = compile(f"host.ipv6 == '{ipv6}'", '', 'eval')
    elif mac is not None:
        condition_compiled = compile(f"host.mac == '{mac}'", '', 'eval')
    else:
        raise Exception("expected one of these: ipv4, ipv6, mac")

    for i in range(len(report[STARRED_HOSTS])):
        host = report[STARRED_HOSTS][i][reface_host.HOST]
        if eval(condition_compiled):
            return host


def insert_other_data(report, data):
    self[OTHER_DATA].update(data)

def find_host(report, ipv4 = None, ipv6=None, mac = None):
    condition_compiled = ""
    if ipv4 is not None:
        condition_compiled = compile(f"host.ipv4 == '{ipv4}'", '', 'eval')
    elif ipv6 is not None:
        condition_compiled = compile(f"host.ipv6 == '{ipv6}'", '', 'eval')
    elif mac is not None:
        condition_compiled = compile(f"host.mac == '{mac}'", '', 'eval')
    else:
        raise Exception("expected one of these: ipv4, ipv6, mac")

    for host in report[HOSTS]:
        if eval(condition_compiled):
            return host


