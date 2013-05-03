#!/bin/bash
################################################################################
#                                                                              # 
#       dev-env.sh - Source this script for poncho development                 #
#                                                                              # 
#       This will update your enviornment's PATH and PYTHONPATH variables      #
#       to point into the poncho working code. You would want to do this       #
#       if you are actively developing the poncho code and don't want to       #
#       run $ python setup.py install all the time.                            #
#                                                                              # 
################################################################################
# env_push enviornment-variable value
env_push() {
    eval value=\$$1
    if [[ $value = "" ]]; then
        export $1=$2
    elif [ -d "$2" ]; then
        tmp=$(echo $value | tr ':' '\n' | awk '$0 != "'"$2"'"' | paste -sd: -)
        if [[ $tmp = "" ]]; then export $1=$2; else export $1=$2:$tmp; fi
    fi
}
# Find the target directorys ( the directory that this file is in )
# and the directory ../lib relative to it.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DIR="$( cd $SCRIPT_DIR/../ && pwd)"
env_push PYTHONPATH $DIR/poncho;
env_push PATH $SCRIPT_DIR
# TODO: Case where user installed .venv
