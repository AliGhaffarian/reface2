import pyroute2
import socket
import pytest
import sys
import os
from test_pyroute2_utilities import *
sys.path.insert(0, os.path.abspath('../..'))

from reface2.utilities.pyroute2_utilities import *
ipr = pyroute2.IPRoute()
ifname="wlan0"

@pytest.mark.parametrize("ifname,ip,expected_errno", generate_pytest_params(params['ifname'], params['ip']))
def test(ifname,ip, expected_errno):
        print(f"called with {ifname=}, {ip=}, {expected_errno=}")


