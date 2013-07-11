#!/usr/bin/env python
import argparse
import os
import prettytable
import re
import subprocess
import tempfile

def _add_arg(f, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""
    if not hasattr(f, 'arguments'):
        f.arguments = []
    if (args, kwargs) not in f.arguments:
        f.arguments.insert(0, (args, kwargs))
 
def arg(*args, **kwargs):
    """Decorator for CLI arguments."""
    def _decorator(func):
        _add_arg(func, *args, **kwargs)
        return func
    return _decorator

def print_table(objs, columns=[], formatters={}):
    table = prettytable.PrettyTable(columns)
    table.aligns = [ 'l' for c in columns ]
    for obj in objs:
        row = []
        for column in columns:
            if column in formatters:
                row.append(formatters[column](obj))
            else:
                field = column.lower().replace(' ', '_')
                row.append(getattr(obj, field, ''))
        table.add_row(row)
    print table.get_string(sortby=columns[0])

class Shell(object):

    def get_base_parser(self):
        desc = self.__doc__ or ''
        parser = argparse.ArgumentParser(description=desc.strip())
        return parser

    def get_subcommand_parser(self):
        parser = self.get_base_parser()
        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        self._find_actions(subparsers)
        return parser

    def _find_actions(self, subparsers):
        for attr in (a for a in dir(self.__class__) if a.startswith('do_')):
            command = attr[3:].replace('_', '-')
            callback = getattr(self.__class__, attr)
            desc = callback.__doc__ or ''
            action_help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])
            subparser = subparsers.add_parser(command,
                help=action_help,
                description=desc,
                add_help=False,
            )
            subparser.add_argument('-h', '--help',
                action='help',
                help=argparse.SUPPRESS,
            )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def main(self, argv):
        parser = self.get_subcommand_parser()
        args = parser.parse_args(argv)
        args.func(self, args)

def get_text_from_editor(template):
    """Enter an editor to gather text. Strip out comment lines."""
    def which(cmd):
        return subprocess.check_output(
            ' '.join(['which', cmd]), shell=True).rstrip()
    editor = os.environ.get('EDITOR', which('vi'))
    with tempfile.NamedTemporaryFile(delete=False) as fh:
        fh.write(template)
        filename = fh.name
    os.system(" ".join([editor, filename]))
    text = []
    comment = re.compile("^#")
    with open(filename, 'r') as fh:
        for line in fh.readline():
            if not comment.match(line):
                text.append(line)
    os.unlink(filename)
    return "\n".join(text) 

