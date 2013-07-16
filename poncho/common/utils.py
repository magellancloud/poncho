#!/usr/bin/env python
"""
poncho.common.utils : Utility Functions
"""
from datetime import datetime

def readable_datetime(dt):
    """Turn a datetime into something readable, with time since or until."""
    if dt is None:
        return ""
    dt = dt.replace(microsecond=0)
    now = datetime.now().replace(microsecond=0)
    low = min(dt, now)
    hi  = max(dt, now)
    delta = hi - low
    relative_times = [ 
        ('year', delta.days // 365),
        ('month', delta.days // 30),
        ('week', delta.days // 7),
        ('day', delta.days),
        ('hour', delta.seconds // 60 // 60 % 24),
        ('min', delta.seconds // 60 % 60),
        ('sec', delta.seconds % 60),
    ]
    modifier = "from now"
    if dt < now:
        modifier = "ago"
    two_sizes = []
    for name,ammount in relative_times:
        if len(two_sizes) == 2:
            break
        if ammount > 0:
            name += "s" if ammount != 1 else ""
            two_sizes.append("%s %s" % (ammount, name))
    if len(two_sizes):
        return "%s (%s %s)" % (dt, ", ".join(two_sizes), modifier)
    return "%s (right now)" % (dt) 
