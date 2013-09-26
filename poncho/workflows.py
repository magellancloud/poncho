# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Poncho service workflow definitions
"""

from oslo.config import cfg

from poncho.nova.manage import nova_manage
from poncho.nova.client import Client

from datetime import datetime
import importlib
import inspect
import sys

DEFAULT_WORKFLOWS = [
    'poncho.workflows.DeleteInstances',
    'poncho.workflows.RestartInstances',
]
opts = [
    cfg.ListOpt('enabled_workflows', default=DEFAULT_WORKFLOWS,
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

    def _get_state_fn(self, state_name):
        return getattr(self.__class__, "state_" + state_name)

    def run(self, thing, context):
        state_name = thing.state
        state_fn = self._get_state_fn(state_name)
        if state_fn:
            return state_fn(self, thing, context)
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
        if datetime.now() > event.begin_passive_drain_at:
            return "passive_drain"

    def state_passive_drain(self, event, ctx):
        instances = []
        for host in event.hosts:
            nova_manage.service_disable(host=host, service='nova-compute')
            instances.append(nova_client.get_host_instances(host))
        for instance in instances:
            have_notified = True
            if not have_notified:
                notifications.notification(
                    timestamp=event.begin_active_drain_at,
                    description=event.description,
                    type='terminate_scheduled',
                    instance_name=instance.name,
                    instance_uuid=instance.uuid).send()
        if datetime.now() > event.begin_active_drain_at:
            return "active_drain"
    
    def state_active_drain(self, event, ctx):
        instances = []
        for host in event.hosts:
            instances.append(nova_client.get_host_instances(host))
        deleting = 0
        for instance in instances:
            if instance.status in ['ACTIVE']:
                deleting += 1
            instance.delete()
            notifications.notification(
                timestamp=datetime.now(),
                description=event.description,
                type='terminating',
                instance_name=instance.name,
                instance_uuid=instance.uuid).send()
        if deleting == 0:
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
