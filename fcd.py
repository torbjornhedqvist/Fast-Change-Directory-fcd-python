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

VERSION = '1.0.0'

class Files: # pylint: disable=too-few-public-methods
    """A class with all predefined filenames as class global attributes used by the program."""

    REPOSITORY = '{}{}'.format(os.path.expanduser("~"), '/.fcd.json')
    DIR = '{}{}'.format(os.path.expanduser("~"), '/.fcd_dir')
    CMD = '{}{}'.format(os.path.expanduser("~"), '/.fcd_cmd')


class TabComplete: # pylint: disable=too-few-public-methods
    """A TAB completer class for readline"""

    def __init__(self, aliases):
        self._aliases = aliases

    def complete(self, text, state):
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


def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser(
        description="(F)ast (C)hange (D)irectory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-a", "--add", type=str, help="add CWD as a new alias")
    group.add_argument("-d", "--delete", type=str, nargs='?', const=True,
                       help="delete an alias")
    parser.add_argument("-c", "--command", type=str, nargs='?', const=True,
                        help="add or update associated command")
    parser.add_argument("-v", "--version", type=str, nargs='?', const=True,
                        help="Print the current version number")
    parser.add_argument('alias', metavar="Alias", type=str, nargs='?',
                        help="Set CWD to the path associated with this alias")
    return vars(parser.parse_args())


def load_repository():
    """Load the repository from file"""
    try:
        file = open(Files.REPOSITORY)
        repository = json.load(file)
        file.close()
        return repository
    except IOError as err:
        sys.exit(err)


def save_repository(repository):
    """Save the current repository in memory to file"""
    try:
        with open(Files.REPOSITORY, 'w') as file:
            json.dump(repository, file)
            file.close()
    except IOError as err:
        sys.exit(err)


def save_for_later_execution(repository, alias):
    """Save the directory path and command, (if not empty) to the two separate files which will
    be used later by the external bash script to change directory and execute the command if
    available."""
    if os.path.isdir(repository[alias]['directory']):
        # The directory path stored in the repository actually exists in the file system, save the
        # directory path to file.
        dir_path = '{}\n'.format(repository[alias]['directory'])
        try:
            file = open(Files.DIR, 'w')
            file.write(dir_path)
            file.close()
        except IOError as err:
            sys.exit(err)

        if repository[alias]['command'] != '':
            # This record have an associated command, save the cmd to file.
            cmd = '{}\n'.format(repository[alias]['command'])
            try:
                file = open(Files.CMD, 'w')
                file.write(cmd)
                file.close()
            except IOError as err:
                sys.exit(err)
    else:
        print('{}Directory "{}" doesn\'t exist, recommended to remove record, aborting!'.format(
            Color.LIGHT_RED, repository[alias]['directory']))
        print(Color.RESET, end='')
        sys.exit(1)


def list_records(records, input_value='', show_cmd=False, use_colors=True):
    """List all alias and directory records"""
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

        if record[0].startswith(input_value):
            if show_cmd is True:
                print("{}[{}] {} : {}".format(current_color, record[0], record[1], record[2]))
            else:
                print("{}[{}] {}".format(current_color, record[0], record[1]))
    print(Color.RESET, end='')


def read_input(completer, hook_message, prompt='fcd> '):
    """Common function to use the tab completer function and read an input line"""
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer.complete)
    def hook():
        readline.insert_text(hook_message)
        readline.redisplay()

    readline.set_pre_input_hook(hook)
    line = input(prompt)
    return line


def alias_handler(args, repository, records, completer):
    """Handles all combinations of aliases provided as argument on command line"""
    if len(sys.argv) == 1:
        # No arguments at all, including alias given from command line
        # Indicates that the user would like to see the full content of the repository and
        # choose an alias from the listed records.
        alias = ''
    else:
        alias = args.get('alias')

    if alias in repository:
        # A complete alias found in repository
        save_for_later_execution(repository, alias)
        #write_alias(repository, alias, Files.DIR, Files.CMD)
    else:
        # Incomplete/partial alias, let's use tab completion
        list_records(records, alias)
        line = None
        hook_message = alias
        while line not in repository:
            line = read_input(completer, hook_message)
            if line not in repository:
                hook_message = line
                list_records(records, line)
        # Now we have a complete alias found in repository
        save_for_later_execution(repository, line)
        #write_alias(repository, line, Files.DIR, Files.CMD)


def add_handler(args, repository):
    """Handles the add command line argument and add a new record with alias, current directory and
    associated command to the repository, (if -c/--command are provided at the same time)."""

    arg_add = args.get('add')
    if arg_add not in repository:
        cmd = ''
        if args.get('command') is not None:
            if args.get('command') is True:
                cmd = input('Provide command to be added: ')
            else:
                cmd = args.get('command')

        add_record = {"directory": os.getcwd(), "command": cmd}
        print('Adding directory "{}" with associated command "{}"'.format(os.getcwd(), cmd))
        repository.update({arg_add : add_record})
        save_repository(repository)
    else:
        print('{}Alias "{}" already exists, aborting!{}'.format(
            Color.LIGHT_RED, arg_add, Color.RESET))
        sys.exit(1)


def delete_handler(args, repository, records, completer):
    """Handles the delete command line argument"""
    arg_delete = args.get('delete')
    if arg_delete is True or arg_delete not in repository:
        # No or incomplete argument provided, let's go into interactive mode
        if arg_delete is True:
            line = '' # tab pre_input_hook empty
        else:
            line = arg_delete
        list_records(records, line)
        while line not in repository:
            line = read_input(completer, line, 'fcd (delete entry)> ')
            if line not in repository:
                list_records(records, line)
        repository.pop(line)
        print("\"{}\" deleted".format(line))
    else:
        # exact argument match found
        repository.pop(arg_delete)
        print("\"{}\" deleted".format(arg_delete))
    save_repository(repository)


def command_handler(args, repository, records, completer):
    """Handles the 'command' command line argument and associates commands which will be
    executed after the change directory have occurred."""
    line = '' # tab pre_input_hook empty
    list_records(records, line, True)
    print("Select which entry to add or update command:")
    while line not in repository:
        line = read_input(completer, line, 'fcd (select entry)> ')
        if line not in repository:
            list_records(records, line, True)
    if args.get('command') is True:
        cmd = input('Provide command to be added or updated: ')
    else:
        cmd = args.get('command')
    repository[line]['command'] = cmd
    print("Updated entry: [{}] {} : {}".format(
        line, repository[line]['directory'], repository[line]['command']))
    save_repository(repository)


def main():
    """Main program"""
    args = parse_args()

    if args.get('version') is True:
        print('v{}'.format(VERSION))
        sys.exit(0)

    # Cleanup from previous execution
    try:
        if os.path.exists(Files.DIR):
            os.remove(Files.DIR)
        if os.path.exists(Files.CMD):
            os.remove(Files.CMD)
    except OSError as err:
        sys.exit(err)

    repository = load_repository()
    aliases = sorted(repository.keys(), key=str.lower) # To be used for tab completion
    completer = TabComplete(aliases)

    # Create a list of all records in alphabetic order which will be used as a helper in
    # combination with the tab completion.
    records = []
    for alias in aliases:
        record = [alias, repository[alias]['directory'], repository[alias]['command']]
        records.append(record)

    if args.get('alias') is not None or len(sys.argv) == 1:
        # A partial or complete alias or no argument at all given from command line
        alias_handler(args, repository, records, completer)

    if args.get('add') is not None:
        add_handler(args, repository)
    elif args.get('delete') is not None:
        # Delete is mutually exclusive with Add
        delete_handler(args, repository, records, completer)

    if args.get('command') is not None and args.get('add') is None:
        # This means a command is provided as an argument, maybe empty, and it's not in combination
        # with an add argument.
        command_handler(args, repository, records, completer)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as err:
        print('Interrupted')
        sys.exit(err)
