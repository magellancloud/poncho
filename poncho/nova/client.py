# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Wrapper for novaclient object construction
"""

from oslo.config import cfg

from novaclient.v1_1 import client as nova_client

cfg.CONF.register_opts([
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node.  This can be an opaque identifier.  '
               'It is not necessarily a hostname, FQDN, or IP address. '
               'However, the node name must be valid within '
               'an AMQP key, and if using ZeroMQ, a valid '
               'hostname, FQDN, or IP address'),
])

OPTIONS = [
    cfg.StrOpt('os-username',
               deprecated_group="DEFAULT",
               default=os.environ.get('OS_USERNAME', 'poncho'),
               help='Username to use for openstack service access'),
    cfg.StrOpt('os-password',
               deprecated_group="DEFAULT",
               secret=True,
               default=os.environ.get('OS_PASSWORD', 'admin'),
               help='Password to use for openstack service access'),
    cfg.StrOpt('os-tenant-id',
               deprecated_group="DEFAULT",
               default=os.environ.get('OS_TENANT_ID', ''),
               help='Tenant ID to use for openstack service access'),
    cfg.StrOpt('os-tenant-name',
               deprecated_group="DEFAULT",
               default=os.environ.get('OS_TENANT_NAME', 'admin'),
               help='Tenant name to use for openstack service access'),
    cfg.StrOpt('os-auth-url',
               deprecated_group="DEFAULT",
               default=os.environ.get('OS_AUTH_URL',
                                      'http://localhost:5000/v2.0'),
               help='Auth URL to use for openstack service access'),
    cfg.StrOpt('os-endpoint-type',
               default=os.environ.get('OS_ENDPOINT_TYPE', 'publicURL'),
               help='Type of endpoint in Identity service catalog to use for '
                    'communication with OpenStack services.'),
]
cfg.CONF.register_cli_opts(OPTIONS, group="service_credentials")

class Client(object):

    def __init__(self):
        """Returns a novaclient object"""
        conf = cfg.CONF.service_credentials
        tenant = conf.os_tenant_id and conf.os_tenant_id or conf.os_tenant_name
        self.nova_client = nova_client.Client(
            username=cfg.CONF.service_credentials.os_username,
            api_key=cfg.CONF.service_credentials.os_password,
            project_id=tenant,
            auth_url=cfg.CONF.service_credentials.os_auth_url,
            endpoint_type=cfg.CONF.service_credentials.os_endpoint_type,
            no_cache=True)

