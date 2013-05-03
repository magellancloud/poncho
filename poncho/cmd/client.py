#!/usr/bin/env python
import argparse
import os
import sys
from novaclient.v1_1 import client

import poncho.annotations
grammar = poncho.annotations.default

def do_add(nova, args):
    (key, value) = args.__dict__['key=value'].split('=')
    # Attempt to validate the key-value pair before adding it
    try:
        annotations.validate(key, value)
    except poncho.annotations.AnnotationSyntaxError as e:
        print >>sys.stderr, e
        sys.exit(1)
    except poncho.annotations.ConstraintSyntaxError as e:
        print >>sys.stderr, e
        sys.exit(1)
    for server_id in args.ids:
        server = nova.servers.get(server_id)
        if server:
            body = { 'meta' : { key : value } }
            nova.servers._create("/servers/%s/metadata/%s" % (server_id, key), body, "meta")
        else:
            print >>sys.stderr, "Server %s not found, skipping!" % (server_id)

def do_remove(nova, args):
    key = args.key
    for server_id in args.ids:
        server = nova.servers.get(server_id)
        if server:
            servers.delete_meta(server, key)
        else:
            print >>sys.stderr, "Server %s not found!" % (server_id)

def do_show(nova, args):
    server = nova.servers.get(args.id)
    print server.metadata

def get_nova_client():
    env = os.environ
    username = env['OS_USERNAME']
    password = env['OS_PASSWORD']
    auth_url = env['OS_AUTH_URL']
    tenant   = env['OS_TENANT_NAME']
    return client.Client(username, password, tenant, auth_url, 
        service_type="compute", endpoint_type="publicURL", insecure=True)

def get_argparse():
    desc = __file__.__doc__ or ''
    parser = argparse.ArgumentParser(
        description = desc.strip(),
        epilog = 'See magellan-annotations help COMMAND'
                 'for help on a specific command.',
    )
    subparsers = parser.add_subparsers(metavar='<subcommand>')
    # Add parser
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument('key=value', help='Annotation to add to instances')
    add_parser.add_argument('ids', nargs='+', help='instance UUIDs to annotate')
    add_parser.set_defaults(callback=do_add)
    # Remove parser
    remove_parser = subparsers.add_parser('remove')
    remove_parser.add_argument('key', help='Annotation to remove from instances')
    remove_parser.add_argument('ids', nargs='+', help='instance UUIDs to annotate')
    remove_parser.set_defaults(callback=do_remove)
    # Show parser
    show_parser = subparsers.add_parser('show')
    show_parser.add_argument('id', help='instance UUID')
    show_parser.set_defaults(callback=do_show)
    return parser

def main():
    try:
        nova = get_nova_client()
        parser = get_argparse()
        args = parser.parse_args()
        callback = args.callback
        callback(nova, args)
    except Exception as e:
        print >>sys.stderr, "ERROR: %s" % unicode(e)
        sys.exit(1)

if __name__ == '__main__':
    main()
