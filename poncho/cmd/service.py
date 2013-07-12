#!/usr/bin/env python
"""service-host : schedule and execute service operationson hosts
running nova-compute
"""
from datetime import datetime, timedelta
import os
import subprocess
import sys
import string
import tempfile

import poncho.workflows
from poncho.common import cli
from poncho.db import api as db
class ServiceShell(cli.Shell):
    "service-host : schedule and execute service operations"

    def __init__(self):
        pass

    def _show_event(self, event):
        # TODO(scott): show host and instance status for each service event
        columns = ['ID', 'Workflow', 'State', 'Created At', 'Description',
            'Notes', 'Passive Drain', 'Active Drain', #'Hosts', 'Instances',
            'Completed', 'Completed At' ]
        column_renames = {'Passive Drain' : 'begin_passive_drain_at',
                          'Active Drain' : 'begin_active_drain_at'}

        def _format_time(dt):
            "Helpful time format: 'ISO-Timestamp (10 mins, 1 sec ago)'"
            if dt is None:
                return ""
            dt = dt.replace(microsecond=0)
            now = datetime.now().replace(microsecond=0)
            low = min(dt, now)
            hi  = max(dt, now)
            delta = hi - low
            relative_times = [ 
                ('year', delta.days // 365),
                ('month', delta.days // 30),
                ('week', delta.days // 7),
                ('day', delta.days),
                ('hour', delta.seconds // 60 // 60 % 24),
                ('min', delta.seconds // 60 % 60),
                ('sec', delta.seconds % 60),
            ]
            modifier = "from now"
            if dt < now:
                modifier = "ago"
            two_sizes = []
            for name,ammount in relative_times:
                if len(two_sizes) == 2:
                    break
                if ammount > 0:
                    name += "s" if ammount != 1 else ""
                    two_sizes.append("%s %s" % (ammount, name))
            if len(two_sizes):
                return "%s (%s %s)" % (dt, ", ".join(two_sizes), modifier)
            return "%s (right now)" % (dt) 

        formatters = {
            'Created At': lambda e: _format_time(e.created_at),
            'Passive Drain': lambda e: _format_time(e.begin_passive_drain_at),
            'Active Drain': lambda e: _format_time(e.begin_active_drain_at),
            'Completed At': lambda e: _format_time(e.completed_at),
            #'Hosts' : lambda e: " ".join([_host_status(h) for h in e.hosts ]),
            #'Instances' : _format_instances,
        }
        align = max(map(len, columns))
        for column in columns:
            attr = column.lower().replace(' ', '_')
            if column in column_renames:
                attr = column_renames[column]
            text = ""
            if column in formatters:
                text = formatters[column](event)
            else:
                text = getattr(event, attr, "")
            print "%s: %s" % (string.rjust(column, align), text)
            

    @cli.arg('--completed', '-c', action='store_true',
        help='Include completed service events')
    def do_list(self, args):
        """Return a list of service events."""
        events = db.get_events()
        fmts = { 'Hosts' : lambda e: ", ".join([ h.name for h in e.hosts]) }
        cli.print_table(events, ['ID', 'Workflow', 'State', 'Hosts'], fmts)

    @cli.arg('service_id', help='The id of the service to show')
    def do_show(self, args):
        """Display details of a service event."""
        event = db.get_event(args.service_id)
        if not event:
            print >>sys.stderr, (
                "Unkown service event '%s'\n" % (args.service_id))
            sys.exit(1)
        self._show_event(event)

    @cli.arg('--hosts', nargs='+', required=True,
        help='Hosts to drain and service.')
    @cli.arg('--delay', type=int, default=0,
        help='Time in minutes to delay the start of the passive drain.')
    @cli.arg('--notify',  type=int, default=60 * 48,
        help='Minimum time in minutes to delay the start of acive draining.')
    @cli.arg('--description', '--desc', type=str,
        help='Description of the service issue; this is sent to users.')
    @cli.arg('--notes', type=str,
        help='Enter notes on the service issue; these are not sent to users.')
    @cli.arg('--dry', action='store_true',
        help='Dry-run mode; this will report the expected service behavior.')
    @cli.arg('--workflow', '-w', required=True,
        help='Specify the workflow to use.')
    def do_create(self, args):
        """Create a new service event."""
        if not args.description:
            # TODO(scott): figure out message templating
            args.description = cli.get_text_from_editor("# fill this in")
        if not args.notes:
            args.notes = ""
        event = db.create_event(args) 
        self._show_event(event)

    def _event_complete(event_id, final_state):
        session = db.get_session()
        event = db.get_event_for_update(event_id, session=session)
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
            self._show_event(event)

    @cli.arg('service_id', help='The id of the service to show')
    def do_complete(self, args):
        """Mark the service event as complete."""
        self._event_complete(args.service_id, 'complete')

    @cli.arg('service_id', help='The id of the service to show')
    @cli.arg('--silent', action='store_true',
        help='Do not notify users that the service event was cancelled')
    def do_cancel(self, args):
        """Cancel the service event."""
        # TODO(scott): implement notifications
        self._event_complete(args.service_id, 'canceled')

    def do_workflow_list(self, args):
        """List available workflows."""
        for workflow in poncho.workflows.get_workflows():
                print workflow.name

    @cli.arg('workflow_name', help='Name of a workflow to show.')
    def do_workflow_show(self, args):
        """Show information about a workflow."""
        workflow = poncho.workflows.get_workflow(args.workflow_name)
        desc = workflow.__doc__ or 'No description provided. :('
        print ("Workflow: %s\n%s\nDescription:\n%s%s\n" %
            (workflow.name, ('=' * 79), desc, ('=' * 79)))


if __name__ == '__main__':
    shell = ServiceShell()
    shell.main(sys.argv[1:])
