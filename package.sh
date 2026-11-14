#!/bin/bash
#
# Copyright (C) Torbjorn Hedqvist - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT license. See LICENSE file in the project
# root for full license information.
#
# Package all required files (new version + the preserved classic version)
# into a tarball and include the current version number in the name.
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

VERSION=$(PYTHONPATH=src python3 -c 'from fcd import VERSION; print(VERSION)') || exit 1
TARBALL="fcd-${VERSION}.tar.gz"

echo "Making a tarball out of the following files"
tar --exclude='__pycache__' -zcvf "$TARBALL" \
    install.sh fcd.sh package.sh README.md LICENSE \
    requirements.txt deploy src classic
echo "Finished, destination tar file contains..."
tar -tvf "$TARBALL"
