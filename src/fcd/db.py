"""Database and file-path handling for Fast Change Directory (fcd).

Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

This module owns all on-disk interaction: the well-known file paths used by the
program (``Files``) and loading/saving the JSON alias database (``Db``). It is
intentionally free of any user-interface concerns.
"""
import json
import logging
import os
import sys

# The database maps an alias (str) to a record dict with "directory" and
# "command" keys. A record value type alias for readability.
Record = dict

logger = logging.getLogger(__name__)


class Files:
    """Predefined filenames used by the program.

    All paths live in the user's home directory. The directory and command
    files form the *sentinel* contract consumed by ``fcd.sh``.
    """

    def __init__(self) -> None:
        logger.debug("Files: Create instance")
        home = os.path.expanduser("~")
        self._db_file = f"{home}/.fcd.json"
        self._dir_file = f"{home}/.fcd_dir"
        self._cmd_file = f"{home}/.fcd_cmd"

    @property
    def db_file(self) -> str:
        """Filename where the database is stored."""
        return self._db_file

    @property
    def dir_file(self) -> str:
        """Filename where the resolved directory path is written."""
        return self._dir_file

    @property
    def cmd_file(self) -> str:
        """Filename where the resolved command is written."""
        return self._cmd_file

    @db_file.setter
    def db_file(self, value: str) -> None:
        logger.debug(value)
        self._db_file = value

    @dir_file.setter
    def dir_file(self, value: str) -> None:
        logger.debug(value)
        self._dir_file = value

    @cmd_file.setter
    def cmd_file(self, value: str) -> None:
        logger.debug(value)
        self._cmd_file = value


class Db:
    """Load and save the JSON alias database.

    Args:
        db_file: Absolute path to the JSON database file.
    """

    def __init__(self, db_file: str) -> None:
        logger.debug("Db: Create instance")
        self._db_file = db_file

    def load(self) -> dict:
        """Load the database from file.

        On first run (file missing) a dummy record is created and persisted so
        the user has an editable starting point. An empty/corrupt file is a
        fatal error, matching the original program behaviour.

        Returns:
            The whole database as a dict mapping alias -> record.
        """
        logger.debug("Enter")
        try:
            if os.path.exists(self._db_file):
                with open(self._db_file, encoding="utf-8") as file:
                    database = json.load(file)
            else:
                print(
                    f"No database {self._db_file} exists in your home directory, "
                    "first time usage?"
                )
                print(
                    "Creates a new database with a dummy record which can be "
                    "removed later."
                )
                database = {"dummy": {"directory": "/dummy", "command": ""}}
                self.save(database)
        except IOError as io_error:
            logger.error(io_error)
            sys.exit(io_error)
        except json.decoder.JSONDecodeError as json_error:
            print(f"{self._db_file} is empty, please delete the file and execute again")
            logger.warning("%s is empty, not allowed", self._db_file)
            sys.exit(json_error)
        logger.debug("Exit: %s", database)
        return database

    def save(self, database: dict) -> None:
        """Persist the in-memory database to file.

        Args:
            database: The full alias -> record mapping to write.
        """
        logger.debug("Enter")
        try:
            with open(self._db_file, "w", encoding="utf-8") as file:
                json.dump(database, file)
        except IOError as io_error:
            logger.error(io_error)
            sys.exit(io_error)
        logger.debug("Exit")
