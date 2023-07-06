#!/usr/bin/env python3
"""
Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

Fast Change Directory (fcd), fcd is a utility program to make it easier to create shortcuts
to frequently visited directories. Since it's impossible to change your shell's current working
directory from within the program this program requires some additional shell scripts,
(included in the database). See the README.md for more information.
"""
import sys
import os
import argparse
import json
import readline

VERSION = '1.1.0'

class Color: # pylint: disable=too-few-public-methods
    """ANSI Colors to be used in terminal output"""
    BLUE = '\033[34m'
    LIGHT_BLUE = '\033[94m'
    RED = '\033[31m'
    LIGHT_RED = '\033[91m'
    CYAN = '\033[96m'
    PURPLE = '\033[95m'
    GREEN = '\033[92m'
    YELLOW = '\033[33m'
    LIGHT_YELLOW = '\033[93m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def parse_args() -> dict:
    """Parse the command line arguments. If any of the rules defined by this function
    is broken, the program will abort with a clear error message given by argparse.

    Returns: vars as a dict with all available arguments as keys.
    """
    parser = argparse.ArgumentParser(
        description="Fast Change Directory (fcd)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-a", "--add", type=str, help="add CWD as a new alias")
    group.add_argument("-d", "--delete", type=str, nargs='?', const=True,
                       help="delete an alias")
    parser.add_argument("-c", "--command", type=str, nargs='?', const=True,
                        help="add or update associated command")
    parser.add_argument("-v", "--version", action='store_true',
                        help="Print the current version number")
    parser.add_argument('alias', metavar="Alias", type=str, nargs='?',
                        help="Set CWD to the path associated with this alias")
    return vars(parser.parse_args())


class Files: # pylint: disable=too-few-public-methods
    """A class with all predefined filenames as class global attributes used by the program."""

    def __init__(self) -> None:
        self._db_file = f'{os.path.expanduser("~")}{"/.fcd.json"}'
        self._dir_file = f'{os.path.expanduser("~")}{"/.fcd_dir"}'
        self._cmd_file = f'{os.path.expanduser("~")}{"/.fcd_cmd"}'

    # All getter methods
    @property
    def db_file(self) -> str:
        """Filename where the database will be stored"""
        return self._db_file

    @property
    def dir_file(self) -> str:
        """Filename where alias matching directory path will be stored"""
        return self._dir_file

    @property
    def cmd_file(self) -> str:
        """Filename where alias matching command will be stored"""
        return self._cmd_file

    # All setter methods
    @db_file.setter
    def db_file(self, value: str) -> None:
        """Set the database filename"""
        self._db_file = value

    @dir_file.setter
    def dir_file(self, value: str) -> None:
        """Set the directory path filename"""
        self._dir_file = value

    @cmd_file.setter
    def cmd_file(self, value: str) -> None:
        """Set the command filename"""
        self._cmd_file = value


class TabComplete: # pylint: disable=too-few-public-methods
    """A TAB completer class for readline

    Args: aliases is a list of strings pulled from the alias keyword in the database and
        will be used for comparison in the complete function provided to readline.
    """

    def __init__(self, aliases: list) -> None:
        self._aliases = aliases

    def complete(self, text: str, state: int) -> str:
        """tab completer function"""
        results = [x for x in self._aliases if x.startswith(text)] + [None]
        return results[state]


class Db:
    """Class to load and save the database file"""

    def __init__(self, db_file: str) -> None:
        self._db_file = db_file

    def load(self) -> dict:
        """Load the database from file

        Returns: database. The whole database as a dict of dicts with records where each
        record is a dict containing the key value pairs of directory and command.
        """
        try:
            if os.path.exists(self._db_file):
                with open(self._db_file, encoding = 'utf-8') as file:
                    database = json.load(file)
            else:
                print(f'{Color.LIGHT_YELLOW}No database {self._db_file} exists ', end='')
                print('in your home directory, first time usage?')
                print('Creates a new database with a dummy record which can be removed later.')
                print(Color.RESET, end='')
                json_string = '{"dummy": {"directory": "/dummy", "command": ""}}'
                database = json.loads(json_string)
                self.save(database)
            return database
        except IOError as io_error:
            sys.exit(io_error)
        except json.decoder.JSONDecodeError as json_decoder_error:
            print(f'{self._db_file} is empty, please delete the file and execute again')
            sys.exit(json_decoder_error)


    def save(self, database: dict) -> None:
        """Save the current database in memory to file
        """
        try:
            with open(self._db_file, 'w', encoding = 'utf-8') as file:
                json.dump(database, file)
        except IOError as io_error:
            sys.exit(io_error)


class Fcd:
    """Main Class for Fast Change Directory (fcd)"""

    def __init__(self) -> None:
        self._files = Files()
        self._db_handler = Db(self._files.db_file)
        self._db = self._db_handler.load()

        # Aliases to be used for tab completion
        self._aliases = sorted(self._db.keys(), key=str.lower)
        # A TabComplete instance prepared with a list of aliases created from all records in the
        # database.
        self._completer = TabComplete(self._aliases)

    def save_for_later_execution(self, alias: str):
        """Save the directory path and command, (if not empty) to the separate files
        self._files.dir_file and self._files.cmd_file. These files will be used later
        by the external bash script to change directory and execute the command if available.

        Args:
            alias: alias as a string which is the key to the record containing the directory
            and commands to be saved.
        """
        if os.path.isdir(self._db[alias]['directory']):
            # The directory path stored in the database actually exists in the file system,
            # save the directory path to file.
            dir_path = f'{self._db[alias]["directory"]}\n'
            try:
                with open(self._files.dir_file, 'w', encoding = 'utf-8') as file:
                    file.write(dir_path)
            except IOError as io_error:
                sys.exit(io_error)

            if self._db[alias]['command'] != '':
                # This record have an associated command, save the cmd to file.
                cmd = f'{self._db[alias]["command"]}\n'
                try:
                    with open(self._files.cmd_file, 'w', encoding = 'utf-8') as file:
                        file.write(cmd)
                except IOError as io_error:
                    sys.exit(io_error)
        else:
            print(f'{Color.LIGHT_RED}Directory "{self._db[alias]["directory"]}" ', end='')
            print(f'doesn\'t exist, recommended to remove record{Color.RESET}')
            sys.exit(1)

    def list_records(self, records: list, alias: str = '', show_cmd: bool = False,
                    use_colors: bool = True) -> None:
        """List all alias and directory records on the console

        Args:
            records: as a list of dict's containing records with alias, directory and command
            alias: As a string to search and list all the records starting with the characters
                in this string.
            show_cmd: Default False. If True it will list the associated commands to each
                record.
            use_colors: Default True and will will toggle the output color if the first character
                changes for the alias in the next record in records. If set to False no colors
                will be used.
        """
        first_char = ''
        if use_colors is True:
            current_color = Color.LIGHT_BLUE
        else:
            current_color = ''

        for record in records:
            if use_colors is True and not record[0].startswith(first_char):
                if current_color == Color.LIGHT_BLUE:
                    current_color = Color.LIGHT_YELLOW
                else:
                    current_color = Color.LIGHT_BLUE
            first_char = record[0][0]

            if record[0].startswith(alias):
                if show_cmd is True:
                    print(f'{current_color}[{record[0]}] {record[1]} : {record[2]}')
                else:
                    print(f'{current_color}[{record[0]}] {record[1]}')
        print(Color.RESET, end='')

    def read_input(self, hook_message: str, prompt: str = 'fcd> ') -> str:
        """Common function to use the tab completer function and read an input line

        Args:
            hook_message: A string containing some prepared text which the completer should
                start to match against the stored list of aliases.
            prompt: A string which will be used as the prompt in the call to input().

        Returns: The output given from the input() call as a string.
        """
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self._completer.complete)
        def hook():
            readline.insert_text(hook_message)
            readline.redisplay()

        readline.set_pre_input_hook(hook)
        line = input(prompt)
        return line

    def alias_handler(self, args: dict, records: list) -> None:
        """Handles all combinations of aliases provided as argument on command line

        Args:
            args: All command line arguments as a dict.
            records: All the records in a sorted alphabetic list

        Returns: None
        """
        if len(sys.argv) == 1:
            # No arguments at all, including alias given from command line
            # Indicates that the user would like to see the full content of the database and
            # choose an alias from the listed records.
            alias = '' # tab pre_input_hook empty
        else:
            alias = args.get('alias')

        if alias in self._db:
            # A complete alias found in database
            self.save_for_later_execution(alias)
        else:
            # Incomplete/partial alias, let's use tab completion
            self.list_records(records, alias)
            while alias not in self._db:
                alias = self.read_input(alias)
                if alias not in self._db:
                    self.list_records(records, alias)
            # Now we have a complete alias found in database
            self.save_for_later_execution(alias)

    def add_handler(self, args: dict) -> None:
        """Handles the add command line argument and add a new record with alias and current
        directory

        Args:
            args: All command line arguments as a dict.

        Returns: None
        """
        arg_add = args.get('add')
        if arg_add not in self._db:
            add_record = {"directory": os.getcwd(), "command": ''}
            print(f'Creating record [{arg_add}] "{os.getcwd()}"')
            self._db.update({arg_add : add_record})
            self._db_handler.save(self._db)
        else:
            print(f'{Color.LIGHT_RED}Alias "{arg_add}" already exists, aborting!{Color.RESET}')
            sys.exit(1)

    def delete_handler(self, args: dict, records: list) -> None:
        """Handles the delete command line argument

        Args:
            args: All command line arguments as a dict.
            records: All the records in a sorted alphabetic list

        Returns: None
        """
        arg_delete = args.get('delete')
        if arg_delete is True or arg_delete not in self._db:
            # No or incomplete argument provided, let's go into interactive mode
            if arg_delete is True:
                alias = '' # tab pre_input_hook empty
            else:
                alias = arg_delete
            self.list_records(records, alias)
            while alias not in self._db:
                alias = self.read_input(alias, 'fcd (delete entry)> ')
                if alias not in self._db:
                    self.list_records(records, alias)
            # Match found through tab completion
            self._db.pop(alias)
            tmp_records = records
            for record in records:
                if record[0] == alias:
                    tmp_records.remove(record)
            records = tmp_records
            print(f'"{alias}" deleted')
        else:
            # Exact argument match found
            self._db.pop(arg_delete)
            tmp_records = records
            for record in records:
                if record[0] == arg_delete:
                    tmp_records.remove(record)
            records = tmp_records
            print(f'"{arg_delete}" deleted')
        self._db_handler.save(self._db)

    def command_handler(self, args: dict, records: list) -> None:
        """Handles the command line argument for adding or updating a 'command' to a record.

        Args:
            args: All command line arguments as a dict.
            records: All the records in a sorted alphabetic list.

        Returns: None
        """
        if args.get('add') in self._db:
            alias = args.get('add')
        else:
            alias = '' # tab pre_input_hook empty
            self.list_records(records, alias, True)
            print("Select which entry to add or update command:")
            while alias not in self._db:
                alias = self.read_input(alias, 'fcd (select entry)> ')
                if alias not in self._db:
                    self.list_records(records, alias, True)

        if args.get('command') is True:
            readline.set_pre_input_hook(None) # reset from previous setting in the read_input above
            cmd = input('Provide command to be added or updated: ')
        else:
            cmd = args.get('command')

        self._db[alias]['command'] = cmd
        print(f'Updated or added command to record: [{alias}] ', end='')
        print(f'{self._db[alias]["directory"]} : {self._db[alias]["command"]}')
        self._db_handler.save(self._db)

    def clean_up(self) -> None:
        """ Cleanup and remove files from previous execution
        """
        try:
            if os.path.exists(self._files.dir_file):
                os.remove(self._files.dir_file)
            if os.path.exists(self._files.cmd_file):
                os.remove(self._files.cmd_file)
        except OSError as io_error:
            sys.exit(io_error)

    def execute(self, args) -> None:
        """ Main Fcd execution
        """

        # Create a list of all records in alphabetic order which will be used as a helper in
        # combination with the tab completion.
        records = []
        for alias in self._aliases:
            record = [alias, self._db[alias]['directory'],
                      self._db[alias]['command']]
            records.append(record)

        try:
            if args.get('alias') is not None or len(sys.argv) == 1:
                # A partial or complete alias or no argument at all given from command line
                self.alias_handler(args, records)

            if args.get('add') is not None:
                self.add_handler(args)
            elif args.get('delete') is not None:
                # Delete is mutually exclusive with Add
                self.delete_handler(args, records)

            if args.get('command') is not None:
                self.command_handler(args, records)
        except KeyboardInterrupt:
            print('Keyboard interrupt')
            sys.exit(1)


def main():
    """Main program"""
    fcd = Fcd()
    fcd.clean_up()

    args = parse_args()
    if args.get('version') is True:
        print(f'v{VERSION}')
        sys.exit(0)

    fcd.execute(args)


if __name__ == '__main__':
    main()
