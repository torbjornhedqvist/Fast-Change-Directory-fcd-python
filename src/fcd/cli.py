"""Command-line entry point for Fast Change Directory (fcd).

Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.
"""
import argparse
import logging
import os
import sys

from fcd import VERSION
from fcd.core import Fcd

logging.basicConfig(
    filename=f'{os.path.expanduser("~")}/fcd.log',
    filemode="a",
    format="%(asctime)s:[%(levelname)s]:%(name)s:%(filename)s:%(funcName)s:"
           "%(lineno)d:(%(message)s)",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def parse_args() -> dict:
    """Parse command-line arguments.

    Returns:
        The parsed arguments as a dict.
    """
    parser = argparse.ArgumentParser(
        description="Fast Change Directory (fcd)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-a", "--add", type=str, help="add CWD as a new alias")
    group.add_argument("-d", "--delete", type=str, nargs="?", const=True,
                       help="delete an alias")
    parser.add_argument("-c", "--command", type=str, nargs="?", const=True,
                        help="add or update associated command")
    parser.add_argument("-v", "--version", action="store_true",
                        help="Print the current version number")
    parser.add_argument("alias", metavar="Alias", type=str, nargs="?",
                        help="Set CWD to the path associated with this alias")
    return vars(parser.parse_args())


def main() -> None:
    """Program entry point."""
    logger.debug("Enter")
    args = parse_args()
    if args.get("version") is True:
        print(f"v{VERSION}")
        sys.exit(0)

    fcd = Fcd()
    fcd.clean_up()
    fcd.args_handler(args)
    logger.debug("Exit")


if __name__ == "__main__":
    main()
