#!/bin/bash
#
# Copyright (C) Torbjorn Hedqvist - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT license. See LICENSE file in the project
# root for full license information.
#
# This script works in conjunction with fcd (the Python program).
# If fcd creates the files below it will
#  a) change directory to the content of ~/.fcd_dir and
#  b) execute the commands in ~/.fcd_cmd
#
# fcd runs from its own dedicated virtual environment, invoked by ABSOLUTE PATH
# so it is independent of whatever virtual environment is active in the current
# shell (no cross-venv conflicts). If that venv interpreter is missing we fall
# back to the system python3, where fcd degrades gracefully to readline.

FCD_VENV_PY="$HOME/bin/fcd-venv/bin/python"
FCD_APP="$HOME/bin/fcd.py"

if [ -x "$FCD_VENV_PY" ]; then
    "$FCD_VENV_PY" "$FCD_APP" "$@"
else
    # Dedicated venv not found; fall back to system python3 (readline UI).
    python3 "$FCD_APP" "$@"
fi
retVal=$?
if [ $retVal -ne 0 ]; then
    # fcd have exited abnormally
    echo "Aborting"
    return $retVal
fi

# Created on succesful call to fcd
if [ -e ~/.fcd_dir ]; then
    fcd_dir=$(<~/.fcd_dir)
    cd "$fcd_dir"
fi

# Created if previous call to fcd had an attached extra command line
if [ -e ~/.fcd_cmd ]; then
    source ~/.fcd_cmd
fi
