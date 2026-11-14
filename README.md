# fcd [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

(F)ast (C)hange (D)irectory for bash shells avoiding a lot of aliases.

## Summary

Tired of adding `cd` aliases for frequently visited directories and then
hunting through your config files to remember what you called them? **fcd**
replaces those tedious aliases with a fast, searchable shortcut database.

**fcd** behaves similarly to a `cd <path>` alias and can also run an extra
command after changing directory (for example `ls -la`). If you forget a
shortcut name, fcd lists all aliases and lets you pick one interactively.

## What's new in this version (1.2.0)

- **Fuzzy matching** — interactive selection now uses subsequence matching, so
  typing `dwn` matches `downloads`. Matches are ranked best-first in a
  live-filtering completion menu you can navigate with the arrow keys.
- **Modern UI via `prompt_toolkit`** — replaces the old one-at-a-time readline
  completion with a visible, scrollable menu.
- **Isolated install** — `prompt_toolkit` is installed into fcd's **own
  dedicated virtual environment**, never into your system Python. The launcher
  calls that venv's interpreter by absolute path, so fcd works the same whether
  or not you are inside some other project's virtual environment, and it can
  never conflict with those environments.
- **Graceful fallback** — if `prompt_toolkit` is unavailable, fcd automatically
  falls back to the classic `readline` (prefix) completion instead of failing.

## Requirements

- bash, GNU coreutils
- Python 3.10+ with the `venv` module (on Debian/Ubuntu/WSL:
  `sudo apt install python3-venv`)
- Internet access the first time you install (to `pip install prompt_toolkit`)

## Installation

### Option 1 — install script (recommended)

```bash
./install.sh
```

This will:

1. create `~/bin` (and add it to your `$PATH` if needed);
2. copy the `fcd.py` launcher, the `fcd` package, and `fcd.sh` into `~/bin`;
3. create a dedicated virtual environment at `~/bin/fcd-venv` and install the
   pinned `prompt_toolkit` into it (the install **fails with a clear message**
   if the venv or dependency install fails — it never silently pollutes your
   system Python);
4. install/refresh the `g`, `g+` and `g-` aliases in `~/.bash_aliases` inside a
   managed, idempotent block (any older `fcd.py`-based `g+`/`g-`/`++` alias
   lines are replaced so you never end up with duplicates).

Log out and back in (or `source ~/.bash_aliases`) and you are ready.

#### Want the original version? Use `--classic`

The original single-file, pure-stdlib fcd (v1.1.0) is preserved unchanged in
the [`classic/`](./classic) directory. Install it instead with:

```bash
./install.sh --classic
```

Run `./install.sh` again without the flag to switch back to the new version.
Both versions use the same `g`, `g+` and `g-` aliases. The classic program
itself (`fcd.py`, `fcd.sh`) is unmodified; only its installer and README were
updated to use `g+`/`g-` instead of the old `++`. Your `~/.fcd.json` database
is shared and never modified by the installer. See `./install.sh --help` for a
summary.

### Option 2 — manual

1. `mkdir -p ~/bin` and ensure `~/bin` is on your `$PATH`.
2. Copy `deploy/fcd.py` (as `fcd.py`), the `src/fcd/` package directory (as
   `fcd/`), `fcd.sh`, `README.md`, and `LICENSE` into `~/bin`.
3. Create the venv and install the dependency:
   ```bash
   python3 -m venv ~/bin/fcd-venv
   ~/bin/fcd-venv/bin/python -m pip install -r requirements.txt
   ```
4. Add these aliases to `~/.bash_aliases`:
   ```bash
   alias g='source ~/bin/fcd.sh "$@"'
   alias g+='"$HOME/bin/fcd-venv/bin/python" "$HOME/bin/fcd.py" -a "$@"'
   alias g-='"$HOME/bin/fcd-venv/bin/python" "$HOME/bin/fcd.py" -d "$@"'
   ```

> **Why `g`?** Simple, `g` for (g)oto ;) — and `g+` / `g-` add and delete.

## Usage

```bash
$ g+ alias     Add the current directory to your list under <alias>.
$ g- [alias]   Delete an entry (pick it interactively if no alias is given).
$ g alias      Change directory to the entry matching <alias> (or part of it).
$ g            List all saved entries and pick one interactively.
               Fuzzy matching + arrow-key selection supported.
```

Attach an extra command to run after the directory change:

```bash
$ g -c <command>     # set the command for an entry
$ g -c               # prompt for the command interactively
```

Delete an entry:

```bash
$ g -d <alias>       # delete a specific entry
$ g -d               # pick the entry to delete interactively
```

More help: `g -h` / `g --help`. Version: `g -v`.

## How it works

fcd cannot change your shell's directory from inside Python, so it writes the
resolved directory to `~/.fcd_dir` (and any command to `~/.fcd_cmd`). The `g`
alias sources `fcd.sh`, which reads those files to perform the actual `cd` and
optionally run the command. This sentinel-file contract is unchanged from
previous versions.

### prompt_toolkit vs. readline

With the dedicated venv present you get the full fuzzy, menu-driven UI. If fcd
is ever run by an interpreter that lacks `prompt_toolkit`, it transparently
falls back to the original `readline` behaviour (strict prefix completion).

## License

MIT — see the `LICENSE` file.
