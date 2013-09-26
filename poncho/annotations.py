""" Grammar rules for validating instance annotations """
# poncho.annotations - Definition of grammar and constraints for
# instance annotations.
import datetime
import re
import time
import urlparse


class AnnotationSyntaxError(Exception):
    def __init__(self, key, value, description):
        self.key = key
        self.value = value
        self.description = description

    def __str__(self):
        return ("Error in annotation: '%s=%s' (%s)" %
                (self.key, self.value, self.description))


class ConstraintSyntaxError(AnnotationSyntaxError):
    def __init__(self, constraint_string, description):
        self.constraint = constraint_string
        self.description = description

    def __str__(self):
        return ("Syntax error in constraint '%s' (%s)" %
                (self.constraint, self.description))


class Grammar(object):

    def __init__(self, tags):
        self.tags = tags

    def validate_server(self, server):
        for tag in self.tags.keys():
            if tag in server.metadata:
                self.validate(tag, self.metadata[tag])
        return True

    def validate(self, key, value):
        if key not in self.tags:
            raise AnnotationSyntaxError(
                key, value, "%s not a valid key name!" % (key))
        if self.tags[key].validate(value):
            return True
        raise AnnotationSyntaxError(
            key, value, "Unknown syntax error with annotation!")

    def list_keys(self):
        return self.tags.keys()

    def explain_values(self, key):
        if key not in self.tags:
            raise AnnotationSyntaxError(
                key, "?", "%s not a valid key name!" % (key))
        elif self.tags[key]:
            return self.tags[key].description()


class Constraint(object):

    def _parse_time(self, string):
        # Parse string of the form (%d[dhms]+) e.g. 510m3s and return a
        # datetime.duration object.
        t = {'d': 0, 'h': 0, 'm': 0, 's': 0}
        regex = re.compile("(\d+)([dhms])")
        for m in regex.finditer(string):
            (ammount, kind) = m.groups()
            t[kind] += int(ammount)
        timedelta = datetime.timedelta(t['d'], t['s'], 0, 0, t['m'], t['h'])
        return self._validate_timedelta(timedelta)

    def _validate_timedelta(self, timedelta):
        zero = datetime.timedelta()
        if timedelta <= zero:
            raise ConstraintSyntaxError(
                self.__class__, "Time interval must be greater than zero!")
        return True


class RuntimeConstraint(Constraint):
    """ 'Runtime(2h12s)' where valid durations are like 0d1h2m3s
    This condition returns true when the instance has been running
    for more than the supplied duraiton.
"""
    def __init__(self, arg_string):
        timedelta = self._parse_time(arg_string)


class NotifiedConstraint(Constraint):
    """ 'Notified(10m)' where valid durations are like 1d2h3m4s
    This indicates that a scheduled-action notification should be
    sent to the notify-url. The constraint returns true when the
    time since the notification was sent is more than the supplied
    duration.
"""
    def __init__(self, arg_string):
        timedelta = self._parse_time(arg_string)


# TimeOfDay helper functions

_time_of_day_regex = re.compile("(?P<start>\d{2}:\d{2}),\s*"
                                "(?P<stop>\d{2}:\d{2})"
                                "(,\s*(?P<tz>[+-]\d{2}:\d{2})){0,1}")
def _parse_time_of_day(string):
    """Returns a 3 tuple (start, stop, tz). Start and stop are datetime.time's
    and tz is a timedelta object."""
    syntax = "Syntax is 't, t[, tz]'. t: 'HH:MM', tz: '+/-HH:MM'."
    match = _time_of_day_regex.match(string)
    if not match:
        raise ConstraintSyntaxError(string, syntax)
    if not match.group('start') or not match.group('stop'):
        raise ConstraintSyntaxError(string, "Must have start and stop times.")
    def to_time(string):
        t = time.strptime(string, "%H:%M")
        return datetime.time(t.tm_hour, t.tm_min)
    def to_timedelta(tz):
        m = re.match("([+-])(\d{2}):(\d{2})", tz)
        if len(m.groups()) != 3:
            raise ConstraintSyntaxError(string, "UTC offset is invalid.")
        (sign, h, m) = m.groups()
        mult = 1 if sign == "+" else -1
        return datetime.timedelta(hours=(mult*int(h)), minutes=(mult*int(m)))
    try:
        start = to_time(match.group('start'))
        stop  = to_time(match.group('stop'))
        tz = to_timedelta(match.group('tz') or '+00:00')
    except:
        raise ConstraintSyntaxError(string, syntax)
    if abs(tz) > datetime.timedelta(days=1):
        raise ConstraintSyntaxError(string,
            "UTC offset must be less than one day.")
    return (start, stop, tz)


class TimeOfDayConstraint(Constraint):
    """ 'TimeOfDay(start, stop [, tz])' where start and stop are
    time strings of the form 'hh:mm' and tz is an optional time
    zone string of the form '+07:30' or '-6:00'. The constraint
    returns true when the time of day is between start and stop
    for the supplied time zone or UTC time.
"""
    def __init__(self, arg_string):
        (start, stop, tz) = _parse_time_of_day(arg_string)
        self.start = start
        self.stop = stop
        self.tz   = tz

    def is_valid(self, context):
        now = datetime.datetime.utcnow() + self.tz
        wraps = True if self.start > self.stop else False
        # Account for case where start and stop wrap around midnight
        if not wraps and self.start < now and now < self.stop:
            return True
        elif wraps and (self.start < now or now < self.stop):
            return True
        return False

def is_url(string):
    try:
        parts = urlparse.urlparse(string)
        assert all([parts.scheme, parts.netloc])
        assert parts.scheme in ['http', 'https']
    except AssertionError:
        return False
    return True


def is_bool(string):
    if type(string) is not str:
        return False
    if string.isdigit() and string in ['1', '0']:
        return True
    if string in ['True', 'False', 'true', 'false']:
        return True
    return False

class Validator(object):
    # TODO(scott): make poncho.annotations.Validator an ABC?
    def validate(self):
        raise NotImplementedError("validate not implemented")
    def description(self):
        raise NotImplemetnedError("validate not implemented")

class KeyValidator(Validator):
    def __init__(self, fn, desc):
        self.fn = fn
        self.desc = desc

    def validate(self, string):
        return self.fn(string)

    def description(self):
        return self.desc


class ConstraintSet(Validator):
    """A string consisting of semicolon delimited list of constraints of
    the following form:

    """
    constraint_regex = re.compile("(\w+)\((\w*)\)")
    constraint_delimiter = ";"

    def __init__(self, constraints):
        self.constraints = constraints

    def make_constraint(self, string):
        m = self.constraint_regex.search(string)
        if m is None or len(m.groups()) != 2:
            raise ConstraintSyntaxError(
                string, "Invalid constraint syntax")

        (name, arg_string) = m.groups()
        constraint_class = self.constraints.get(name, None)
        if constraint_class is None:
            raise ConstraintSyntaxError(
                string, "Could not find constraint class for %s" % (name))
        return constraint_class(arg_string)

    def make_constraints(self, string):
        parts = string.split(self.constraint_delimiter)
        if len(parts) == 1 and parts[0] == "":
            return []
        return [self.make_constraint(p) for p in parts]

    def validate(self, string):
        self.make_constraints(string)
        return True

    def description(self):
        docs = [self.__doc__]
        for c in self.constraints.values():
            docs.append(c.__doc__)
        return "\n".join(docs)

_constraints = ConstraintSet({
    'Runtime': RuntimeConstraint, # depreciated
    'MinRuntime' : RuntimeConstraint,
    'Notified': NotifiedConstraint,
    'TimeOfDay' : TimeOfDayConstraint,
     })

default = Grammar({
    'reboot_when': _constraints,
    'terminate_when': _constraints,
    'ha_group_id': KeyValidator(
        lambda x: True if len(x) else False, "Any unique string"),
    'ha_group_min': KeyValidator(str.isdigit, "A positive integer"),
    'priority': KeyValidator(str.isdigit, "A positive integer"),
    'snapshot_on_terminate': KeyValidator(is_bool, "'True' or 'False'"),
    'notify_url': KeyValidator(is_url, "A valid URL"),
})
