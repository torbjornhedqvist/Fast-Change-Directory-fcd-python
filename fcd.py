#!/usr/bin/env python3
"""
Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

(F)ast (C)hange (D)irectory, fcd is a utility program to make it easier to create shortcuts
to frequently visited directories. Since it's impossible to change your shell's current working
directory from within the program this program requires some additional shell scripts,
(included in the repository). See the README.md for more information.
"""
import sys
import os
import argparse
import json
import readline

VERSION = '1.0.1'

class Files: # pylint: disable=too-few-public-methods
    """A class with all predefined filenames as class global attributes used by the program."""

    # REPOSITORY = '{}{}'.format(os.path.expanduser("~"), '/.fcd.json')
    REPOSITORY = f'{os.path.expanduser("~")}{"/.fcd.json"}'
    # DIR = '{}{}'.format(os.path.expanduser("~"), '/.fcd_dir')
    DIR = f'{os.path.expanduser("~")}{"/.fcd_dir"}'
    # CMD = '{}{}'.format(os.path.expanduser("~"), '/.fcd_cmd')
    CMD = f'{os.path.expanduser("~")}{"/.fcd_cmd"}'

class TabComplete: # pylint: disable=too-few-public-methods
    """A TAB completer class for readline

    Args: aliases is a list of strings pulled from the alias keyword in the repository and
        will be used for comparison in the complete function provided to readline.
    """

    def __init__(self, aliases: list):
        self._aliases = aliases

    def complete(self, text: str, state: int) -> str:
        """tab completer function"""
        results = [x for x in self._aliases if x.startswith(text)] + [None]
        return results[state]


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
        description="(F)ast (C)hange (D)irectory",
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


def load_repository() -> dict:
    """Load the repository from file

    Returns: repository. The whole repository as a dict of dicts with records where each
        record is a dict containing the key value pairs of directory and command.
    """
    status = 0
    try:
        if os.path.exists(Files.REPOSITORY):
            with open(Files.REPOSITORY, encoding = 'utf-8') as file:
                repository = json.load(file)
        else:
            print(f'{Color.LIGHT_YELLOW}No repository {Files.REPOSITORY} exists in your ', end='')
            print('home directory, first time usage?')
            print('Creates a new repository with a dummy record which can be removed later.')
            print(Color.RESET, end='')
            json_string = '{"dummy": {"directory": "/dummy", "command": ""}}'
            repository = json.loads(json_string)
            save_repository(repository)
        return repository
    except IOError as io_error:
        sys.exit(io_error)
    except json.decoder.JSONDecodeError as json_decoder_error:
        print(f'{Files.REPOSITORY} is empty, please delete it and it will be created properly')
        sys.exit(json_decoder_error)

def save_repository(repository: dict):
    """Save the current repository in memory to file

    Args:
        repository: The whole repository as a dict of dicts with records where each
            record is a dict containing the key value pairs of directory and command.
    """
    try:
        with open(Files.REPOSITORY, 'w', encoding = 'utf-8') as file:
            json.dump(repository, file)
    except IOError as io_error:
        sys.exit(io_error)


def save_for_later_execution(repository: dict, alias: str):
    """Save the directory path and command, (if not empty) to the separate files Files.DIR
    and Files.CMD. These files will be used later by the external bash script to change
    directory and execute the command if available.

    Args:
        repository: The whole repository as a dict of dicts with records.
        alias: alias as a string which is the key to the record containing the directory
            and commands to be saved.
    """
    if os.path.isdir(repository[alias]['directory']):
        # The directory path stored in the repository actually exists in the file system, save the
        # directory path to file.
        dir_path = f'{repository[alias]["directory"]}\n'
        try:
            with open(Files.DIR, 'w', encoding = 'utf-8') as file:
                file.write(dir_path)
        except IOError as io_error:
            sys.exit(io_error)

        if repository[alias]['command'] != '':
            # This record have an associated command, save the cmd to file.
            cmd = f'{repository[alias]["command"]}\n'
            try:
                with open(Files.CMD, 'w', encoding = 'utf-8') as file:
                    file.write(cmd)
            except IOError as err:
                sys.exit(err)
    else:
        print(f'{Color.LIGHT_RED}Directory "{repository[alias]["directory"]}" doesn\'t exist,\
 recommended to remove record, aborting!{Color.RESET}')
        sys.exit(1)


def list_records(records: list, alias: str = '', show_cmd: bool = False,
                 use_colors: bool = True):
    """List all alias and directory records

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


def read_input(completer: TabComplete, hook_message: str, prompt: str = 'fcd> ') -> str:
    """Common function to use the tab completer function and read an input line

    Args:
        completer: A TabComplete instance prepared with a list of aliases created from
            all records in the repository.
        hook_message: A string containing some prepared text which the completer should
            start to match against the stored list of aliases.
        prompt: A string which will be used as the prompt in the call to input().

    Returns: The output given from the input() call as a string.
    """
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.complete)
    def hook():
        readline.insert_text(hook_message)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    line = input(prompt)
    return line


def alias_handler(args: dict, repository: dict, records: list, completer: TabComplete):
    """Handles all combinations of aliases provided as argument on command line

    Args:
        args: All command line arguments as a dict.
        repository: The whole repository as a dict of dicts with records.
        records: All the records in a sorted alphabetic list
        completer: A TabComplete instance prepared with a list of aliases created from
            all records in the repository.
    """
    if len(sys.argv) == 1:
        # No arguments at all, including alias given from command line
        # Indicates that the user would like to see the full content of the repository and
        # choose an alias from the listed records.
        alias = '' # tab pre_input_hook empty
    else:
        alias = args.get('alias')

    if alias in repository:
        # A complete alias found in repository
        save_for_later_execution(repository, alias)
    else:
        # Incomplete/partial alias, let's use tab completion
        list_records(records, alias)
        while alias not in repository:
            alias = read_input(completer, alias)
            if alias not in repository:
                list_records(records, alias)
        # Now we have a complete alias found in repository
        save_for_later_execution(repository, alias)


def add_handler(args: dict, repository: dict):
    """Handles the add command line argument and add a new record with alias and current directory

    Args:
        args: All command line arguments as a dict.
        repository: The whole repository as a dict of dicts with records.
    """
    arg_add = args.get('add')
    if arg_add not in repository:
        add_record = {"directory": os.getcwd(), "command": ''}
        print(f'Creating record [{arg_add}] "{os.getcwd()}"')
        repository.update({arg_add : add_record})
        save_repository(repository)
    else:
        print(f'{Color.LIGHT_RED}Alias "{arg_add}" already exists, aborting!{Color.RESET}')
        sys.exit(1)


def delete_handler(args: dict, repository: dict, records: list, completer: TabComplete):
    """Handles the delete command line argument

    Args:
        args: All command line arguments as a dict.
        repository: The whole repository as a dict of dicts with records.
        records: All the records in a sorted alphabetic list
        completer: A TabComplete instance prepared with a list of aliases created from
            all records in the repository.
    """
    arg_delete = args.get('delete')
    if arg_delete is True or arg_delete not in repository:
        # No or incomplete argument provided, let's go into interactive mode
        if arg_delete is True:
            alias = '' # tab pre_input_hook empty
        else:
            alias = arg_delete
        list_records(records, alias)
        while alias not in repository:
            alias = read_input(completer, alias, 'fcd (delete entry)> ')
            if alias not in repository:
                list_records(records, alias)
        # Match found through tab completion
        repository.pop(alias)
        tmp_records = records
        for record in records:
            if record[0] == alias:
                tmp_records.remove(record)
        records = tmp_records
        print(f'"{alias}" deleted')
    else:
        # Exact argument match found
        repository.pop(arg_delete)
        tmp_records = records
        for record in records:
            if record[0] == arg_delete:
                tmp_records.remove(record)
        records = tmp_records
        print(f'"{arg_delete}" deleted')
    save_repository(repository)


def command_handler(args: dict, repository: dict, records: list, completer: TabComplete):
    """Handles the command line argument for adding or updating a 'command' to a record.

    Args:
        args: All command line arguments as a dict.
        repository: The whole repository as a dict of dicts with records.
        records: All the records in a sorted alphabetic list
        completer: A TabComplete instance prepared with a list of aliases created from
            all records in the repository.
    """
    if args.get('add') in repository:
        alias = args.get('add')
    else:
        alias = '' # tab pre_input_hook empty
        list_records(records, alias, True)
        print("Select which entry to add or update command:")
        while alias not in repository:
            alias = read_input(completer, alias, 'fcd (select entry)> ')
            if alias not in repository:
                list_records(records, alias, True)

    if args.get('command') is True:
        readline.set_pre_input_hook(None) # reset from previous setting in the read_input above
        cmd = input('Provide command to be added or updated: ')
    else:
        cmd = args.get('command')

    repository[alias]['command'] = cmd
    print(f'Updated or added command to record: [{alias}] ', end='')
    print(f'{repository[alias]["directory"]} : {repository[alias]["command"]}')
    save_repository(repository)


def main():
    """Main program"""

    # Cleanup from previous execution
    try:
        if os.path.exists(Files.DIR):
            os.remove(Files.DIR)
        if os.path.exists(Files.CMD):
            os.remove(Files.CMD)
    except OSError as io_error:
        sys.exit(io_error)

    args = parse_args()

    if args.get('version') is True:
        print(f'v{VERSION}')
        sys.exit(0)

    repository = load_repository()
    aliases = sorted(repository.keys(), key=str.lower) # To be used for tab completion
    completer = TabComplete(aliases)

    # Create a list of all records in alphabetic order which will be used as a helper in
    # combination with the tab completion.
    records = []
    for alias in aliases:
        record = [alias, repository[alias]['directory'], repository[alias]['command']]
        records.append(record)

    try:
        if args.get('alias') is not None or len(sys.argv) == 1:
            # A partial or complete alias or no argument at all given from command line
            alias_handler(args, repository, records, completer)

        if args.get('add') is not None:
            add_handler(args, repository)
        elif args.get('delete') is not None:
            # Delete is mutually exclusive with Add
            delete_handler(args, repository, records, completer)

        if args.get('command') is not None:
            command_handler(args, repository, records, completer)
    except KeyboardInterrupt as kb_interrupt:
        print('Keyboard interrupt')
        sys.exit(1)

if __name__ == '__main__':
    main()
