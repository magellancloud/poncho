import sys
import poncho.common.cli as cli

class AdminShell(cli.Shell):
    """poncho-admin : administrative interface to poncho"""
    def do_test(self, args, ctx):
        """testing this command"""
        pass

def main():
    obj = AdminShell()
    AdminShell().main(sys.argv[1:])

if __name__ == '__main__':
    main()
