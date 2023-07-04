#!/bin/bash
#
# Copyright (C) Torbjorn Hedqvist - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT license. See LICENSE file in the project
# root for full license information.
#
# This script works in conjunction with fcd.py
# If fcd.py creates the files below it will
#  a) change directory to the content of ~/.fcd_dir and
#  b) execute the commands in ~/.fcd_cmd
#
fcd.py $@
retVal=$?
if [ $retVal -ne 0 ]; then
    # fcd.py have exited abnormally
    echo "Aborting"
    return $retVal
fi


# Created on succesful call to fcd.py
if [ -e ~/.fcd_dir ]; then
    cd `cat ~/.fcd_dir`
fi

# Created if previous call to fcd.py had an attached extra command line
if [ -e ~/.fcd_cmd ]; then
    source ~/.fcd_cmd
fi
