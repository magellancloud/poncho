""" Grammar rules for validating instance annotations """
# poncho.annotations - Definition of grammar and constraints for
# instance annotations.
import datetime
import re
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

_constraints = ConstraintSet(
    {'Runtime': RuntimeConstraint, 'Notified': NotifiedConstraint})

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
