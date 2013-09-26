# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Poncho Manager - handles service event operations.
"""

from oslo.config import cfg

from poncho import annotations as annotations
from poncho.db import api as db
from poncho import notifications as notifications
from poncho import workflows as workflows
#import poncho.nova.client
#import poncho.nova.manage

class ServiceEventManager(object):
    def create_event(self, args):
        return db.create_event(args)
     
    def _event_complete(event_id, final_state):
        session = db.get_session()
        event = db.get_event_for_update(event_id, session=session)
        # TODO(scott): switch these to exceptions
        if not event:
            print >>sys.stderr, "Unknown event '%s'" % (event_id)
        if event.completed:
            print >>sys.stderr, "Cancel failed: event already compelted."
            session.rollback()
        else:
            event.completed = True
            event.state = final_state 
            event.completed_at = datetime.now().replace(microsecond=0)
            session.commit()
        return event
    def complete_event(self, event_id):
        return self._event_complete(event_id, 'complete')

    def cancel_event(self, event_id, silent=False):
        # TODO(scott): implement event-canceled notifications
        return self._event_complete(event_id, 'canceled')
    
    def _calculate_event_notify_delay(self, event):
        instances = self.get_event_instances(event)
        requested = None
        max_delay = None
        delays = [requested]
        for instance in instances:
            wanted = self.annotation_manager.get_notification_delay(
                instance, event_type=event)
            if wanted:
                delays.append(wanted)
        return min(max_delay, max(delays))

    def disable_event_hosts(self, event):
        for host in event.hosts:
            se


    
