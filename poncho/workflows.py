# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Poncho service workflow definitions
"""
import importlib
import inspect
import sys
from oslo.config import cfg

DEFAULT_WORKFLOWS = [
    'poncho.workflows.DeleteInstances',
    'poncho.workflows.RestartInstances',
]
opts = [
    cfg.StrOpt('enabled_workflows', default=DEFAULT_WORKFLOWS,
        help="Avaliable workflows for Poncho service event operations"),
]
CONF = cfg.CONF
CONF.register_opts(opts)

class UnknownState(Exception):
    def __init__(self, state):
        self.state = state
    def __str__(self):
        return "Unknown state '%s'" % (self.state)

class Workflow(object):
    def name(self):
        return self.__class__.name

    def states(self):
        return [ fn_name[6:] for fn_name in dir(self.__class__)
                if fn_name.startswith('state_')]

    def _get_state_fn(self, state):
        return getattr(self.__class__, "state_" + state_name)

    def run(self, thing, context):
        state_name = thing.state()
        state_fn = self._get_state_fn(state)
        if state_fn:
            return self.state_fn(thing, context)
        else:
            raise UnknownState(state_name)

class RestartInstances(Workflow):
    """ Notify, then shutdown instances. Restart after service.

initalized -> notify -> active_drain -> drained -> restarting -> completed
 * canceled

"""
    name = "restart-instances"
    pass

class DeleteInstances(Workflow):
    """ Workflow for deleting instances on hosts.

initalized -> passive_drain -> active_drain -+
                     |                       |
                     +-----> drained <-------+
                                |
    * canceled              compleded
"""
    name = "delete-instances"
    def __init__(self):
        pass

    def state_initialized(self, event, ctx):
        delay_elapsed = False
        if delay_elapsed:
            return "passive_drain"

    def state_passive_drain(self, event, ctx):
        hosts = []
        for host in hosts:
            # disable host
            pass
        find_instances = []
        for instance in find_instances:
            have_notified = True
            if not have_notified:
                # notify user
                pass
        passive_elapsed = False
        if passive_elapsed:
            return "active_drain"
    
    def state_active_drain(self, event, ctx):
        find_instances = []
        for instance in find_instances:
            # delete_instance
            pass
        hosts = []
        for host in hosts:
            # disable host
            pass
        drain_complete = False
        if drain_complete:
            return "drained"

    def state_drained(self, event, ctx):
        pass

    def state_complete(self, event, ctx):
        pass

    def state_canceled(self, event, ctx):
        pass

def get_workflows():
    return _ENABLED_WORKFLOWS.values()

def get_workflow(workflow_name):
    if workflow_name in _ENABLED_WORKFLOWS:
        return _ENABLED_WORKFLOWS[workflow_name]
    else:
        raise Exception("Unknown workflow '%s', did you add it to the config?"
            % (wokflow_name))

def _enabled_workflows():
    workflows = {}
    for path in CONF.enabled_workflows:
        parts = path.split('.')
        module = ".".join(parts[:len(parts)-1])
        cls = parts[len(parts)-1]
        try:
            module = importlib.import_module(module)
            workflow = getattr(module, cls)
            workflows[workflow.name] = workflow
        # TODO(scott): want to log failed workflow imports
        except ImportError, e:
            pass
        except KeyError, e:
            pass
    return workflows

_ENABLED_WORKFLOWS = _enabled_workflows()
