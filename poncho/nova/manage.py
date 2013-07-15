# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Wrapper for nova-manage invocation
"""

from oslo.config import cfg

import subprocess

OPTIONS = [
    cfg.StrOpt('command_wrapper', default='{placeholder}'
               help="This wrapper is for invoking the nova-manage command"),
]

CONF = cfg.CONF
CONF.register_opts(OPTIONS)

class NovaManageWrapper(object):
    """Wrapper for nova-manage command."""
    def __init__(self):
        self.command_format = CONF.command_wrapper

    def _wrap_command(self, command):
        return self.command_format.format({ 'placeholder' :command }) 

    def _call_wrapped(self, command):
        final = self._wrap_command(command)
        stdout=None
        rtv = subprocess.call(final.split(), stdout=stdout)
        return stdout

    def service_list(self):
        txt = self._call_wrapped(" ".join(['nova-manage', 'service', 'list'])) 
        return txt

    def _alter_service(self, which, host=None, service=None):
        if not host or not service:
            raise Exception("Need to call with host and service kwargs")
        args = ['nova-manage', 'service', which, '--host=%s' % (host),
                '--service=%s' % (service)]
        txt = self._call_wrapped(" ".join(args))
        return txt

    def service_enable(self, **kwargs):
        return self._alter_service('enable', **kwargs)

    def service_disable(self, **kwargs):
        return self._alter_service('disable', **kwargs)
