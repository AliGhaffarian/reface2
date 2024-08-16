import string
import subprocess
import errno
import os

"""
all functionalities that i didnt find a good library for and decided to use shell instead
"""

def get_sysctl_param(param):    
    return int(subprocess.check_output(["sysctl", param]).decode().split(' ')[2].strip())

def set_sysctl_param(param, value):
    if not isinstance(value,int):
        e = Exception(errno.EINVAL, os.strerror(errno.EINVAL))
        raise e
    out = subprocess.check_output(["sudo", "sysctl", f"{param}={value}"]).decode().strip()
    if out != f"{param} = {value}":
        return 1
    return 0
