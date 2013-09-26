from nose.tools import *

import poncho.notifications as pn
from datetime import datetime
import sys

def test_notification_constructor():
    n = pn.notification(
        timestamp=datetime.now(), description="", type="reboot_scheduled",
        instance_uuid="UUID", instance_name="NAME") 
    isinstance(n, pn.RebootScheduled)
    isinstance(str(n), str)
    n = pn.notification(
        timestamp=datetime.now(), description="", type="rebooting",
        instance_uuid="UUID", instance_name="NAME") 
    isinstance(n, pn.Rebooting)
    isinstance(str(n), str)
    n = pn.notification(
        timestamp=datetime.now(), description="", type="terminate_scheduled",
        instance_uuid="UUID", instance_name="NAME") 
    isinstance(n, pn.TerminateScheduled)
    isinstance(str(n), str)
    n = pn.notification(
        timestamp=datetime.now(), description="", type="terminating",
        instance_uuid="UUID", instance_name="NAME") 
    isinstance(n, pn.Terminating)
    isinstance(str(n), str)
