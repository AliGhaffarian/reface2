import time

ALIAS = "alias"
HOST = "host"
COMMENT = "comment"
OTHER_DATA = "other_data"


def make_reface_host(alias = "", host = "", comment = [], other_data = {}):
    return {
            ALIAS : alias,
            #nmap host type
            HOST : host,
            COMMENT : comment,
            OTHER_DATA : other_data
            }

def add_comment(host, comment):
    host[COMMENT].append((comment, time.ctime()))

