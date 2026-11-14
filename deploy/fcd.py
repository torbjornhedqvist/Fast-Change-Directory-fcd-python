#!/usr/bin/env python3
"""Launcher shim for Fast Change Directory (fcd).

Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

The actual implementation lives in the ``fcd`` package installed alongside this
file (in ``~/bin``). This shim makes ``~/bin`` importable and delegates to
``fcd.cli.main`` so the program can be launched as ``fcd.py`` by the shell
integration (``fcd.sh`` / the ``g+`` and ``g-`` aliases).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# pylint: disable=wrong-import-position,cyclic-import
# (This standalone launcher file happens to be named fcd.py; it is NOT the
# package __init__, so the fcd -> fcd.cli import is not a real cycle.)
from fcd.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
