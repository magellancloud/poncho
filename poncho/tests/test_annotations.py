from nose.tools import *
import datetime
from poncho import annotations as pa



def test_anntations():
    grammar = pa.default
    assert grammar.validate("reboot_when", "Runtime(2h)")
    assert grammar.validate("reboot_when", "MinRuntime(2h)")
    assert grammar.validate("terminate_when", "Notified(3m)")
    assert grammar.validate("terminate_when", "Notified(3m);Runtime(4h)")
    assert grammar.validate("terminate_when", "Notified(3m);MinRuntime(4h)")
    assert grammar.validate("ha_group_id", "foobar")
    assert grammar.validate("terminate_when", "")
    assert grammar.validate("reboot_when", "")
    assert grammar.validate("priority", "32")
    assert grammar.validate("notify_url", "https://example.com/notify")
    assert grammar.validate("snapshot_on_terminate", "True")
    assert grammar.validate("snapshot_on_terminate", "False")

def test_bad_annotations():
    grammar = pa.default
    assert_raises(pa.AnnotationSyntaxError, grammar.validate, "foo", "bar")
    assert_raises(pa.ConstraintSyntaxError, grammar.validate, "reboot_when", "Runner()")
    assert_raises(pa.ConstraintSyntaxError, grammar.validate, "reboot_when", "Runtime(foo)")
    assert_raises(pa.ConstraintSyntaxError, grammar.validate, "reboot_when", "Notified(foo)")
    assert_raises(pa.ConstraintSyntaxError, grammar.validate, "terminate_when", "Notified(foo)")
    assert_raises(pa.ConstraintSyntaxError, grammar.validate, "reboot_when", "Runtime;Notified")
    assert_raises(pa.AnnotationSyntaxError, grammar.validate, "priority", "foo")
    assert_raises(pa.AnnotationSyntaxError, grammar.validate, "ha_group_min", "bar")
    assert_raises(pa.AnnotationSyntaxError, grammar.validate, "notify_url", "notanumber")
    assert_raises(pa.AnnotationSyntaxError, grammar.validate, "snapshot_on_terminate", "bin")
    assert_raises(pa.AnnotationSyntaxError, grammar.validate, "snapshot_on_terminate", True)

def test_descriptions():
    grammar = pa.default
    assert True, isinstance( grammar.explain_values("reboot_when"), str )
    # currently have 6 keys in grammar
    assert 6, len(grammar.list_keys())
    assert_raises(pa.AnnotationSyntaxError, grammar.explain_values, "foobar")

def check_string(string):
    assert True, isinstance( string )

def test_each_description():
    grammar = pa.default
    for key in grammar.list_keys():
        yield check_string, grammar.explain_values(key)

def test_time_calculation():
    c = pa.MinRuntimeConstraint("45m")
    assert datetime.timedelta(minutes=45), c._parse_time("45m")
    assert datetime.timedelta(days=1), c._parse_time("1d")
    assert_raises(pa.AnnotationSyntaxError, c._validate_timedelta, datetime.timedelta())

def test_is_bool():
    assert pa.is_bool("True")
    assert pa.is_bool("0")
    assert pa.is_bool("false")
    assert False == pa.is_bool("")
    assert False == pa.is_bool("43")

def test_time_of_day_parser():
    valid = [ "22:00, 06:00", "22:00, 06:30", "22:00,06:30", "06:30,12:00",
              "22:00, 06:00, +06:00", "22:00, 06:30, +11:00",
              "22:00,06:30,+04:00", "22:00,06:30,-04:00",
              "22:00, 06:00, -06:00", "22:00, 06:30, -11:00",
              "23:00,06:00,+23:00", ]
    for case in valid:
        (start, stop, tz) = pa._parse_time_of_day(case)
    invalid = [ "24:00, 06:00", "23:00,6:30", "23:61, 23:00", "asdfasdf",
            "234:44:22, 2343", "23:00,6:00, 01:00", "23:00,06:00,+25:00" ]
    for case in invalid:
        assert_raises(pa.ConstraintSyntaxError, pa._parse_time_of_day, case)
    t = lambda h,m: datetime.time(h,m)
    tz = lambda z: datetime.timedelta(hours=z/60, minutes=z%60)
    def t(h,m):
        return datetime.time(h,m)
    check_results = {
        "22:00,06:30,+04:00" : (t(22,00), t(6,30), tz(4*60)),
        "22:00,06:30,-04:00" : (t(22,00), t(6,30), tz(-4*60)),
        "22:00, 06:00, -06:00" : (t(22,00), t(6,00), tz(-6*60)),
        "12:35, 05:59, -11:30" : (t(12,35), t(5,59), tz(-11*60-30)),
    }
    for case,expected in check_results.iteritems():
        print pa._parse_time_of_day(case)
        print expected
        assert pa._parse_time_of_day(case) == expected
        
