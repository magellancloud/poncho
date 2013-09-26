# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Notification library for system events.
"""

from oslo.config import cfg

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import importlib
import re
import requests
import smtplib
import string
import sys

DEFAULT_NOTIFICATIONS = [
    'poncho.notifications.RebootScheduled',
    'poncho.notifications.Rebooting',
    'poncho.notifications.TerminateScheduled',
    'poncho.notifications.Terminating',
    'poncho.notifications.SnapshotCreated',
    'poncho.notifications.HaGroupDegraded',
    'poncho.notifications.HaGroupHealthy',
    'poncho.notifications.ShedLoadRequest',
]

notify_group = cfg.OptGroup(name='notify', title='Notification options')
notify_group_options = [
    cfg.StrOpt(
        'enabled_notifications', default=DEFAULT_NOTIFICATIONS,
        help="Types of notifications sent out."),
    cfg.StrOpt(
        'default_notification_delay', default='1h',
        help='For scheduled notifications, e.g. "reboot-scheduled", this is '
        'the default ammount of time after being notified that the reboot can '
        'take place.'),
    cfg.StrOpt(
        'maximum_notification_delay', default='24h',
        help='For scheduled notifications, e.g. "reboot-scheduled", this is '
        'the maximum time that the system will delay the event for.'),
    cfg.BoolOpt(
        'enable_notifications_by_mail', default=True,
        help="If no notify_url is supplied, send notifications by email."),
    cfg.StrOpt(
        'email_notifications_from_addr',
        help="Email address to send notifications from"),
    cfg.StrOpt(
        'email_notifications_reply_to',
        help="Reply_To header."),
    cfg.StrOpt(
        'email_notifications_subject', default='OpenStack Notification',
        help="Subject for notification email messages."),
    cfg.StrOpt(
        'email_notifications_smtp_server',
        help='SMTP server to use when sending notification emails'),
]

CONF = cfg.CONF
CONF.register_group(notify_group)
for opt in notify_group_options:
    CONF.register_opt(opt, group=notify_group)

def email_body(notification):
    reply = (CONF.email_notifications_reply_to or
        CONF.email_notifications_from)
    return """%s
    The reason given for this event was:
    %s

    This notification is automatically generated.
    Please direct any questions to %s.
    """ % (notification, notification.description, reply)

def _send_email(to_addrs=[], subject="", body="", files=[]):
    assert type(to_addrs)==list
    assert type(files)==list
    from_addr = CONF.email_notifications_from_addr
    smtp_server = CONF.email_notifications_smtp_server
    assert type(from_addr)==str
    assert type(smtp_server)==str
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = COMMASPACE.join(to_addrs)
    if CONF.get('email_notifications_reply_to', None):
        msg['Reply-To'] = CONF.email_notifications_reply_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach( MIMEText(body) )
    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)
    smtp = smtplib.SMTP(smtp_server)
    smtp.sendmail(from_addr, to_addrs, msg.as_string())
    smtp.close()
    
def notification(**kwargs):
    """Factory to generate a new notification object"""
    def convert(name):
        return "".join(map(string.capitalize, name.split('_')))
    if "type" not in kwargs:
        raise InvalidNotification()
    class_name = convert(kwargs["type"])
    module = importlib.import_module(__name__)
    class_obj = getattr(module, class_name)
    return class_obj(**kwargs)
    
class InvalidNotification(Exception):
    pass
    
class Notification(object):
    required_keys = set(['timestamp', 'description', 'type'])
    def __init__(self, **kwargs):
        for key in self.required_keys:
            if key not in kwargs:
                raise InvalidNotification("kwarg %s required" % key)
            else:
                setattr(self, key, kwargs[key])

    def __str__(self):
        """Representation used for sending emails."""
        raise NotImplementedError()

    def as_json(self):
        """Format as json structure"""
        body = {}
        for key in self.required_keys:
            body[key] = self.key
        return json.dumps(body)
    
    def notify_urls(self):
        """Return an array of notify_urls applicaable to this event.""" 
        raise NotImplementedError()
    
    def notify_emails(self):
        """Return an array of emails addresses applicable to this event."""
        raise NotImplementedError()
    
    def send(self):
        urls = self.notify_urls()
        if len(urls) > 0:
            data = self.as_json()
            headers = { 'content-type' : 'application/json' }
            for url in urls:
                r = requests.post(url, data=data, headers=headers)
                # TODO(scott): check status and retry? possibly a queue?
        else:
            emails = self.notifiy_urls()
            body = email_body(self)
            from_addr=CONF.email_notifications_from
            # TODO(scott): reasonable subject fields
            _send_email(to_addrs=emails, subject="Subject", body=body)
    

class InstanceNotification(Notification):
    required_keys = (Notification.required_keys |
                     set(['instance_name', 'instance_uuid']))
    def notify_urls(self):
        metadata = nova.servers.get(self.instance_uuid).meta
        if 'notify_url' in metadata:
            return [ metadata['notify_url'] ]
        else:
            return []
 
    def notify_emails(self):    
        owner = nova.servers.get(self.instance_uuid).user_id
        if owner:
            email = keystone.users.get(owner).email
            if email:
                return [email]
        return []
    
        
class RebootScheduled(InstanceNotification):
   def __str__(self):
        return """The instance "${instance_name}" \
(UUID: ${instance_uuid}) will reboot at ${timestamp}.""" % (self)
    

class Rebooting(InstanceNotification) :
    def __str__(self):
        return """The instance "${instance_name}" \
(UUID: ${instance_uuid}) rebooted at ${timestamp}.""" % (self)


class TerminateScheduled(InstanceNotification):
    def __str__(self):
        return """The instance "${instance_name}" \
(UUID: ${instance_uuid}) will be terminated at ${timestamp}.""" % (self)


class Terminating(InstanceNotification):
    def __str__(self):
        return """The instance "${instance_name}" \
(UUID: ${instance_uuid}) was terminated at ${timestamp}.""" % (self)


class SnapshotCreated(InstanceNotification):
    required_keys = (InstanceNotification.required_keys |
                     set(['snapshot_name', 'snapshot_id']))
    def __str__(self):
        """A snapshot of "${instance_name}" \
(UUID: ${instance_uuid}) was created at ${timestamp}.
Snapshot Name: ${snapshot_name}
Snapshot ID: ${snapshot_id}""" % (self)


class TenantWide(Notification):
    required_keys = (Notification.required_keys |
                     set(['ha_group_id', 'ha_group_active_count',
                     'ha_group_active_list', 'tenant_id']))
    def notify_urls(self):
        servers = [ server for server in nova.servers.list()
            if server.tenant_id == self.tenant_id ]
        urls = set()
        for server in servers:
            if 'notify_url' in server.meta:
                urls |= server.meta['notify_url']
        return urls
    def notify_emails(self):
        # TODO(scott): Figure out how to get admin users from tenant
        emails = set()
        return emails


class HaGroupDegraded(TenantWide):
    def __str__(self):
        return """The HA group ${ha_group_id} went into \
degraded mode at ${timestamp} with ${ha_group_active_count} instances active.
Active instances: ${ha_group_active_list}
""" % (self)


class HaGroupHealthy(TenantWide):
    def __str__(self):
        return """The HA group ${ha_group_id} transitioned \
to a healthy state at ${timestamp} with ${ha_group_active_count} instances \
active.
Active instances: ${ha_group_active_list}
""" % (self)


class ShedLoadRequest(TenantWide):
    def __str__(self):
        return """This is a load shedding request. \
Please delete any idle or unneeded instances.""" % (self)
