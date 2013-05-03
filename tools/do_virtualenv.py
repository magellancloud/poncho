#!/usr/bin/env python
import os
import subprocess
import sys


def main(args):
    top = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    venv = os.path.join(top, '.venv') 
    run_command(['virtualenv', '-q', venv])

if __name__ == '__main__':
    main(sys.argv)
