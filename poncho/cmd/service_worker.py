#!/usr/bin/env python
"""service-worker : daemon that is responsible for iterating through existing
service events and performing operations when possible.
"""
import argparse
import daemon
import time
import sys
import poncho.db.api as db
import poncho.db.models
import poncho.workflows

from oslo.config import cfg

opts = [
    cfg.StrOpt('polling_interval', default=2,
        help='Interval in seconds to update workflows for service events.'),
]
CONF = cfg.CONF
CONF.register_opts(opts)

def main_loop(context):
    while True:
        session = db.get_session() 
        # Get service events that are not completed
        events = db.get_events()
        for event in events:
            event = db.get_event_for_update(event.id, session)
            print "Event %d state: %s..." % (event.id, event.state)
            try:
                workflow_name = event.workflow
                workflow = poncho.workflows.get_workflow(workflow_name)
                newstate = workflow().run(event, {})
                if newstate:
                    print "Event %d state: %s -> %s" % (event.id, event.state, newstate)
                    event.state = newstate
                else:
                    print "Event %d state: %s -X" % (event.id, event.state)

            #except Exception, e:
            #    print "Event %d, exception: %s" % (event.id, e)
            #    # TODO(scott): implement logging
            #    pass
            finally:
                session.commit()
        time.sleep(CONF.polling_interval)


def main():
    context = None
    main_loop(context)

if __name__ == '__main__':
    poncho.db.models.BASE.metadata.create_all(db.get_engine())
    main()
