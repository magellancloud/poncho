#!/usr/bin/env python
"""poncho : lightweight tools for full clouds

You must source an OpenStack .novarc file before these commands
will work. The following environment variables must be defined:
OS_USERNAME, OS_PASSWORD, OS_AUTH_URL, OS_TENANT_NAME.

"""
import argparse
from novaclient.v1_1 import client
import os
import sys

from poncho.annotations import default as grammar
from poncho.annotations import AnnotationSyntaxError


def do_add(nova, args):
    (key, value) = args.__dict__['key=value'].split('=')
    # Attempt to validate the key-value pair before adding it
    try:
        annotations.validate(key, value)
    except poncho.annotations.AnnotationSyntaxError as e:
        print >>sys.stderr, e
        sys.exit(1)
    for server_id in args.ids:
        server = nova.servers.get(server_id)
        if server:
            body = {'meta': {key: value}}
            nova.servers._create("/servers/%s/metadata/%s" %
                                 (server_id, key), body, "meta")
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


def do_annotation_help(nova, args):
    keys = grammar.list_keys()
    if args.key and args.key in keys:
        s = "Documentation for annotation using key '%s':\n" % args.key
        print s + grammar.explain_values(args.key)
    else:
        print "Keys: \n" + "\n".join(keys)


def get_nova_client():
    try:
        username = os.environ['OS_USERNAME']
        password = os.environ['OS_PASSWORD']
        auth_url = os.environ['OS_AUTH_URL']
        tenant = os.environ['OS_TENANT_NAME']
        c = client.Client(
            username, password, tenant, auth_url, service_type="compute",
            endpoint_type="publicURL", insecure=True)
        return c
    except KeyError, e:
        print >>sys.stderr, (
            "Environment variable %s not defined!\n" 
            "Have you sourced your OpenStack .novarc file?\n"
            % (e))
        sys.exit(1)


def get_argparse():
    desc = __doc__ or ''
    parser = argparse.ArgumentParser(
        description=desc.strip(),
        epilog='See poncho "annotation-help" for docs on valid annotations'
    )
    subparsers = parser.add_subparsers(
        title='Commands')

    # Add parser
    add_parser = subparsers.add_parser(
        "add", help="Annotate instance(s) with metadata")
    add_parser.add_argument(
        '--key', required=True,
        help='Annotation to add to instances')
    add_parser.add_argument(
        '--value', required=True,
        help="Annotation value. See 'annotation-help' for documentation")
    add_parser.add_argument(
        'ids', nargs='+',
        help='instance UUIDs to annotate')
    add_parser.set_defaults(callback=do_add)

    # Remove parser
    remove_parser = subparsers.add_parser(
        'remove', help="Remove annotation from instance(s)")
    remove_parser.add_argument(
        'key',
        help='Annotation to remove from instances')
    remove_parser.add_argument(
        'ids', nargs='+',
        help='instance UUIDs to annotate')
    remove_parser.set_defaults(callback=do_remove)

    # Show parser
    show_parser = subparsers.add_parser(
        'show', help="Show annotations set on instance")
    show_parser.add_argument('id', help='instance UUID')
    show_parser.set_defaults(callback=do_show)

    # Help parser
    help_parser = subparsers.add_parser(
        'annotation-help', help="Documentation for instance annotations")
    help_parser.add_argument(
        'key', nargs='?', help="Get usage documentation for a specific key")
    help_parser.set_defaults(callback=do_annotation_help)
    return parser


def main():
    try:
        nova = get_nova_client()
        parser = get_argparse()
        if len(sys.argv) < 2:
            parser.print_help()
            sys.exit()
        args = parser.parse_args()
        if args.callback:
            args.callback(nova, args)
        else:
            parser.print_help()
    except Exception as e:
        print >>sys.stderr, "ERROR: %s" % unicode(e)
        sys.exit(1)

if __name__ == '__main__':
    main()
