# Implementation Documentation

## Abstract

This is a simple implementation description of the code, just as a quick
recap to myself when I haven't touched this project for some months ;)

## A flowchart describing the main flow of execution.

![](./fcd-flowchart-main.png)

## parse_args

Creates a Python "argparse" construct with all valid arguments which can be
provided from the command line.
Returns a dictionary with the values of all arguments. Dependent if they are
mandatory or optional they can have a value of `None`, `True` or a string
value.

## load_repository

This function will load the repository into a python dictionary from the
JSON formatted repository file `~/.fcd.json`

This is an example of the format of this file:

```json
{
  "fcd": {
    "directory": "/home/etorhed/repos/Fast-Change-Directory-fcd-python",
    "command": ""
  },
  "dl": {
    "directory": "/mnt/c/Users/etorhed/Downloads",
    "command": "ll"
  }
}
```

## alias_handler
When no argument or an alias is provided at command line this function is
called. The alias provided at command line doesn't have to be complete, it
can be just the beginning of an alias and with TAB completion the rest can
easily be filled in by the function. It will loop until a valid alias is
found in the repository or you abort the program with Ctrl-C.

When an alias is found alias_handler will call a separate function:

```python
def save_for_later_execution(repository, alias):
```

which will create a file, `~/.fcd_dir` inserting the directory path associated
with the alias. As an example if we refer to the repository example above and
the alias **dl** is provided the content of the file would be:

```text
/mnt/c/Users/etorhed/Downloads
```

In this example it will also create a file, `~/.fcd_cmd` for the associated
command `ll` as this is not empty and the content would be:

```text
ll
```

If any of these two files exists after execution, and this program `fcd.py`
is called from the external bash script `fcd.sh`, they will be sourced and
change the directory in the parent shell and execute the command provided.

## add_handler

TBD