"""Core orchestration for Fast Change Directory (fcd).

Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

Holds the :class:`Fcd` orchestrator that ties the database, selector and
user-interface together and writes the sentinel files consumed by ``fcd.sh``.
Collaborators (``Db`` and ``Selector``) are injected to keep the class testable.
"""
import logging
import os
import sys

from fcd.db import Db, Files
from fcd.selectors import Selector, get_selector
from fcd.ui import Color, list_records

logger = logging.getLogger(__name__)


class Fcd:
    """Main orchestrator for Fast Change Directory.

    Args:
        files: Optional :class:`Files` instance (created if omitted).
        db_handler: Optional :class:`Db` instance (created if omitted).
        selector: Optional :class:`Selector`; created via
            :func:`fcd.selectors.get_selector` if omitted.
    """

    def __init__(self, files: Files | None = None, db_handler: Db | None = None,
                 selector: Selector | None = None) -> None:
        logger.debug("Fcd: Create instance")
        self._color = Color()
        self._files = files or Files()
        self._db_handler = db_handler or Db(self._files.db_file)
        self._db = self._db_handler.load()
        self._aliases = sorted(self._db.keys(), key=str.lower)
        self._selector = selector or get_selector(self._aliases)

    def _select_until_valid(self, prefill: str, records: list, prompt: str,
                            show_cmd: bool = False) -> str:
        """Loop prompting the user until a known alias is entered.

        Args:
            prefill: Initial text for the input line.
            records: Records to (re)list between attempts.
            prompt: The prompt string.
            show_cmd: Whether listings should include commands.

        Returns:
            A valid alias present in the database.
        """
        alias = prefill
        while alias not in self._db:
            alias = self._selector.select(alias, prompt)
            if alias not in self._db:
                list_records(records, alias, show_cmd, color=self._color)
        return alias

    def save_for_later_execution(self, alias: str) -> None:
        """Write the directory (and optional command) sentinel files.

        Args:
            alias: The alias whose record should be resolved and written.
        """
        logger.debug("Enter")
        directory = self._db[alias]["directory"]
        if os.path.isdir(directory):
            dir_path = f"{directory}\n"
            try:
                with open(self._files.dir_file, "w", encoding="utf-8") as file:
                    logger.debug('Write "%s" to %s', dir_path, self._files.dir_file)
                    file.write(dir_path)
            except IOError as io_error:
                logger.error(io_error)
                sys.exit(io_error)

            if self._db[alias]["command"] != "":
                cmd = f'{self._db[alias]["command"]}\n'
                try:
                    with open(self._files.cmd_file, "w", encoding="utf-8") as file:
                        logger.debug('Write "%s" to %s', cmd, self._files.cmd_file)
                        file.write(cmd)
                except IOError as io_error:
                    logger.error(io_error)
                    sys.exit(io_error)
        else:
            print(
                f'{self._color.light_red}Directory "{directory}" '
                f"doesn't exist, recommended to remove record{self._color.reset}"
            )
            logger.warning("%s doesn't exist", directory)
            sys.exit(1)
        logger.debug("Exit")

    def _records(self) -> list:
        """Build the sorted ``[alias, directory, command]`` record list."""
        records = []
        for alias in self._aliases:
            records.append([
                alias,
                self._db[alias]["directory"],
                self._db[alias]["command"],
            ])
        return records

    def alias_handler(self, alias: str, records: list) -> None:
        """Resolve an alias (exact or interactive) and write sentinel files.

        Args:
            alias: A complete, partial or empty alias.
            records: Pre-built record list for listings.
        """
        if not isinstance(alias, str):
            raise ValueError(f"Invalid type: {type(alias)}")
        if not isinstance(records, list):
            raise ValueError(f"Invalid type: {type(records)}")
        logger.debug('Enter: alias="%s"', alias)

        alias = alias.rstrip("/")
        if alias in self._db:
            self.save_for_later_execution(alias)
        else:
            list_records(records, alias, color=self._color)
            alias = self._select_until_valid(alias, records, "fcd> ")
            self.save_for_later_execution(alias)
        logger.debug("Exit")

    def add_handler(self, arg_add: str) -> None:
        """Add the current working directory under a new alias.

        Args:
            arg_add: The alias name to create.
        """
        if not isinstance(arg_add, str):
            raise ValueError(f"Invalid type: {type(arg_add)}")
        logger.debug("Enter: arg_add=%s", arg_add)

        arg_add = arg_add.rstrip("/")
        if "/" in arg_add:
            print(
                f'{self._color.light_red}Alias "{arg_add}" is invalid, '
                f'"/" is not allowed in an alias name, aborting!{self._color.reset}'
            )
            logger.warning('Alias "%s" contains "/", not allowed', arg_add)
            sys.exit(1)

        if arg_add not in self._db:
            add_record = {"directory": os.getcwd(), "command": ""}
            print(f'Creating record [{arg_add}] "{os.getcwd()}"')
            self._db.update({arg_add: add_record})
            self._db_handler.save(self._db)
        else:
            print(
                f'{self._color.light_red}Alias "{arg_add}" already exists, '
                f"aborting!{self._color.reset}"
            )
            logger.warning('Alias "%s" already exists, aborting!', arg_add)
            sys.exit(1)
        logger.debug("Exit")

    def delete_handler(self, arg_delete, records: list) -> None:
        """Delete a record (exact or interactive).

        Args:
            arg_delete: Complete/partial alias string, or ``True`` when ``-d``
                is given with no value.
            records: Pre-built record list for listings.
        """
        logger.debug("Enter: arg_delete=%s", arg_delete)

        if arg_delete is not True:
            if not isinstance(arg_delete, str):
                raise ValueError(f"Invalid type: {type(arg_delete)}")
            arg_delete = arg_delete.rstrip("/")

        if arg_delete is True or arg_delete not in self._db:
            alias = "" if arg_delete is True else arg_delete
            list_records(records, alias, color=self._color)
            alias = self._select_until_valid(alias, records, "fcd (delete entry)> ")
        else:
            alias = arg_delete

        self._db.pop(alias)
        print(f'"{alias}" deleted')
        self._db_handler.save(self._db)
        logger.debug("Exit")

    def command_handler(self, args: dict, records: list) -> None:
        """Add or update the command associated with a record.

        Args:
            args: Parsed command-line arguments.
            records: Pre-built record list for listings.
        """
        if not isinstance(args, dict):
            raise ValueError(f"Invalid type: {type(args)}")
        if not isinstance(records, list):
            raise ValueError(f"Invalid type: {type(records)}")
        logger.debug("Enter: cmd=%s", args.get("command"))

        if args.get("add") in self._db:
            alias = args.get("add")
        else:
            list_records(records, "", show_cmd=True, color=self._color)
            print("Select which entry to add or update command:")
            alias = self._select_until_valid("", records, "fcd (select entry)> ",
                                              show_cmd=True)

        if args.get("command") is True:
            cmd = self._read_command("Provide command to be added or updated: ")
        else:
            cmd = args.get("command")

        self._db[alias]["command"] = cmd
        print(
            f"Updated or added command to record: [{alias}] "
            f'{self._db[alias]["directory"]} : {self._db[alias]["command"]}'
        )
        self._db_handler.save(self._db)
        logger.debug("Exit")

    def _read_command(self, prompt: str) -> str:
        """Read a free-text command via the selector, else plain input()."""
        reader = getattr(self._selector, "read_command", None)
        if callable(reader):
            return reader(prompt)
        return input(prompt)

    def clean_up(self) -> None:
        """Remove sentinel files left over from a previous execution."""
        logger.debug("Enter")
        try:
            if os.path.exists(self._files.dir_file):
                os.remove(self._files.dir_file)
            if os.path.exists(self._files.cmd_file):
                os.remove(self._files.cmd_file)
        except OSError as io_error:
            logger.error(io_error)
            sys.exit(io_error)
        logger.debug("Exit")

    def args_handler(self, args: dict) -> None:
        """Dispatch based on parsed command-line arguments.

        Args:
            args: Parsed command-line arguments as a dict.
        """
        logger.debug("Enter")
        records = self._records()
        try:
            alias = args.get("alias")
            if alias is not None or len(sys.argv) == 1:
                if len(sys.argv) == 1:
                    alias = ""
                self.alias_handler(alias, records)

            if args.get("add") is not None:
                self.add_handler(args.get("add"))
            elif args.get("delete") is not None:
                self.delete_handler(args.get("delete"), records)

            if args.get("command") is not None and args.get("delete") is None:
                self.command_handler(args, records)
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            logger.info("Keyboard interrupt")
            sys.exit(1)
        logger.debug("Exit")
