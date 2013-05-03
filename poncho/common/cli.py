#!/usr/bin/env python
import argparse

def arg(*args, **kwargs):
    def _decorator(func):
        _add_arg(func, *args, **kwargs)
        return func
    return _decorator

def _add_arg(f, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""
    if not hasattr(f, 'arguments'):
        f.arguments = []
    if (args, kwargs) not in f.arguments:
        f.arguments.insert(0, (args, kwargs))

class Shell(object):
    subcommands = {}
    epilog = ''
    def get_base_parser(self):
        desc = self.__doc__ or ''
        parser = argparse.ArgumentParser(
            description=desc.strip(),
            epilog=self.epilog or ''
        )
        self.parser = parser
        return parser

    def get_subcommand_parser(self):
        parser = self.get_base_parser()
        subcommands = self.subcommands
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        self._find_actions(subparsers, self.__class__)
        for command_name, command_class in subcommands.iteritems():
            self._find_actions(subparsers, command_class)
        return parser

    def _find_actions(self, subparsers, actions_class):
        for attr in (a for a in dir(actions_class) if a.startswith('do_')):
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_class, attr)
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
    def do_help(self, args):
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
        else:
            self.parser.print_help()

    def get_ctx(self):
        return {}
    def main(self, argv):
        parser = self.get_subcommand_parser()
        args = parser.parse_args(argv) 
        ctx = self.get_ctx()
        if options.help or not argv:
            parser.print_help()
            return 0
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        args.command(self, args, ctx)
