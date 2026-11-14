#!/bin/bash
#
# Copyright (C) Torbjorn Hedqvist - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT license. See LICENSE file in the project
# root for full license information.
#
# Installer for fcd (Fast Change Directory).
#
#   ./install.sh             Install the new version (prompt_toolkit UI, fuzzy
#                            matching) with its own dedicated virtual
#                            environment. This is the default.
#   ./install.sh --classic   Install the original, pure-stdlib version that is
#                            kept unchanged in the classic/ directory.
#   ./install.sh --help      Show this help.
#
# You can switch between the two by simply running the installer again with or
# without --classic. Your alias database (~/.fcd.json) is never touched.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FCD_VENV="$HOME/bin/fcd-venv"
FCD_VENV_PY="$FCD_VENV/bin/python"
ALIASES_FILE="$HOME/.bash_aliases"

usage() {
    cat <<'USAGE_EOF'
Usage: ./install.sh [--classic] [--help]

  (no option)   Install the new fcd (prompt_toolkit UI + fuzzy matching) in its
                own dedicated virtual environment.
  --classic     Install the original classic fcd (pure stdlib, readline
                completion) from the classic/ directory. It gets the same
                g / g+ / g- aliases as the new version.
  -h, --help    Show this help and exit.

Running the installer again with or without --classic switches between the
two versions. The alias database ~/.fcd.json is never modified.
USAGE_EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
classic=false
for arg in "$@" ; do
    case "$arg" in
        --classic)
            classic=true
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            echo >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ -z "${HOME:-}" ] ; then
    echo "\$HOME not set which is required for installation to work properly."
    echo "Bailing out..."
    exit 1
fi

# ---------------------------------------------------------------------------
# Remove the managed alias block written by the new installer, if present.
# ---------------------------------------------------------------------------
remove_managed_aliases() {
    if [ -f "$ALIASES_FILE" ] && grep -q '# >>> fcd aliases >>>' "$ALIASES_FILE" ; then
        sed -i '/# >>> fcd aliases >>>/,/# <<< fcd aliases <<</d' "$ALIASES_FILE"
        echo "Removed the managed fcd alias block from $ALIASES_FILE."
    fi
}

# ---------------------------------------------------------------------------
# Write the managed alias block (g, g+, g-) for the given version.
#   new      aliases call fcd's dedicated venv interpreter by absolute path
#   classic  aliases call the pure-stdlib fcd.py found via $PATH (as before)
# Idempotent: any previous managed block and any legacy un-managed fcd aliases
# (++, g+, g-, g) are replaced, so re-runs and switching never duplicate.
# ---------------------------------------------------------------------------
write_managed_aliases() {
    local mode="$1" add_cmd del_cmd comment
    if [ "$mode" = "new" ] ; then
        add_cmd='"$HOME/bin/fcd-venv/bin/python" "$HOME/bin/fcd.py" -a "$@"'
        del_cmd='"$HOME/bin/fcd-venv/bin/python" "$HOME/bin/fcd.py" -d "$@"'
        comment="All aliases call fcd's dedicated venv interpreter by absolute path"
    else
        add_cmd='fcd.py -a "$@"'
        del_cmd='fcd.py -d "$@"'
        comment="Classic version: aliases call the pure-stdlib fcd.py found on PATH"
    fi

    if [ ! -f "$ALIASES_FILE" ] ; then
        echo "# File created by fcd installation script" > "$ALIASES_FILE"
        echo "" >> "$ALIASES_FILE"
    fi

    remove_managed_aliases
    sed -i "/alias ++='fcd.py -a/d" "$ALIASES_FILE"
    sed -i "/alias g+='fcd.py -a/d" "$ALIASES_FILE"
    sed -i "/alias g-='fcd.py -d/d" "$ALIASES_FILE"
    sed -i "/alias g='source ~\/bin\/fcd.sh/d" "$ALIASES_FILE"

    {
        echo ""
        echo "# >>> fcd aliases >>>"
        echo "# Managed by fcd install.sh ($mode version) - safe to regenerate."
        echo "# $comment."
        echo "#   g   go to a directory      g+  add current directory      g-  delete an alias"
        printf '%s\n' "alias g='source ~/bin/fcd.sh \"\$@\"'"
        printf '%s\n' "alias g+='$add_cmd'"
        printf '%s\n' "alias g-='$del_cmd'"
        echo "# <<< fcd aliases <<<"
    } >> "$ALIASES_FILE"
    echo "Installed/updated the g, g+ and g- aliases ($mode version, managed block)."
}

# ===========================================================================
# CLASSIC installation
# ===========================================================================
if [ "$classic" = true ] ; then
    echo "Installing the CLASSIC version of fcd (from $SCRIPT_DIR/classic)."

    # Clean up anything specific to the new version so the two never mix. The
    # classic installer only adds aliases when none exist, so the managed block
    # must go first.
    remove_managed_aliases
    if [ -d "$HOME/bin/fcd" ] ; then
        rm -rf "$HOME/bin/fcd"
        echo "Removed the new fcd package from $HOME/bin/fcd."
    fi
    if [ -d "$FCD_VENV" ] ; then
        echo "Note: the new version's virtual environment is left in place at"
        echo "      $FCD_VENV (unused by classic). Remove it with: rm -rf $FCD_VENV"
    fi

    # The classic installer copies its files relative to the current directory.
    # It is run completely unmodified; it adds the original '++' alias, which we
    # then replace with the same g / g+ / g- aliases the new version uses.
    cd "$SCRIPT_DIR/classic" || { echo "classic/ directory not found."; exit 1; }
    bash ./install.sh
    classic_rc=$?
    if [ $classic_rc -ne 0 ] ; then
        exit $classic_rc
    fi
    write_managed_aliases classic
    exit 0
fi

# ===========================================================================
# NEW installation (default)
# ===========================================================================
cd "$SCRIPT_DIR" || exit 1
echo "Installing the NEW version of fcd (use --classic for the original)."

if ! command -v python3 >/dev/null 2>&1 ; then
    echo "python3 not found on PATH, required to create the fcd venv."
    echo "Bailing out..."
    exit 1
fi
echo "All prerequisites are OK, let's start the installation."

update=false

# ---------------------------------------------------------------------------
# ~/bin directory
# ---------------------------------------------------------------------------
if [ ! -d "$HOME/bin" ] ; then
    echo "Creating $HOME/bin directory"
    if ! mkdir "$HOME/bin" ; then
        echo "Failed to create $HOME/bin directory. Can't continue."
        echo "Bailing out..."
        exit 1
    fi
else
    echo "User already has a $HOME/bin directory, no need to create."
fi

if [ ! -w "$HOME/bin" ] ; then
    if ! chmod u+w "$HOME/bin" ; then
        echo "Failed to make $HOME/bin writable. Can't continue."
        echo "Bailing out..."
        exit 1
    fi
fi

if [ -e "$HOME/bin/fcd.py" ] ; then
    echo "Seems you have an old installation, replacing with new installation."
    update=true
fi

# ---------------------------------------------------------------------------
# Copy program files (shim + package + helper script + docs)
# ---------------------------------------------------------------------------
echo "Copying the fcd files to $HOME/bin."
cp ./deploy/fcd.py "$HOME/bin" || { echo "Copy of fcd.py failed."; exit 1; }
cp ./fcd.sh "$HOME/bin" || { echo "Copy of fcd.sh failed."; exit 1; }
rm -rf "$HOME/bin/fcd"
cp -r ./src/fcd "$HOME/bin/fcd" || { echo "Copy of fcd package failed."; exit 1; }
find "$HOME/bin/fcd" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
cp ./README.md "$HOME/bin/fcd-README.md" 2>/dev/null || true
cp ./LICENSE "$HOME/bin/fcd-LICENSE" 2>/dev/null || true

echo "Making the scripts executable."
chmod u+x "$HOME/bin/fcd.py" "$HOME/bin/fcd.sh"
chmod ugo-x "$HOME/bin/fcd-README.md" "$HOME/bin/fcd-LICENSE" 2>/dev/null || true

# ---------------------------------------------------------------------------
# Dedicated virtual environment (fail hard on any failure)
# ---------------------------------------------------------------------------
echo "Creating dedicated virtual environment at $FCD_VENV"
if [ ! -d "$FCD_VENV" ] ; then
    if ! python3 -m venv "$FCD_VENV" ; then
        echo "ERROR: Failed to create the fcd virtual environment at $FCD_VENV."
        echo "Ensure the python3 'venv' module is available (e.g. apt install"
        echo "python3-venv) and re-run install.sh. Bailing out..."
        exit 1
    fi
else
    echo "Reusing existing venv at $FCD_VENV"
fi

echo "Installing pinned dependencies into the fcd venv."
if ! "$FCD_VENV_PY" -m pip install --upgrade pip >/dev/null ; then
    echo "ERROR: Failed to upgrade pip inside the fcd venv. Bailing out..."
    exit 1
fi
if ! "$FCD_VENV_PY" -m pip install -r ./requirements.txt ; then
    echo "ERROR: Failed to install fcd dependencies (requirements.txt) into"
    echo "the fcd venv. fcd will not have its enhanced UI. Bailing out..."
    exit 1
fi
echo "Dependencies installed into the isolated fcd venv."

# ---------------------------------------------------------------------------
# $PATH: ensure ~/bin is present
# ---------------------------------------------------------------------------
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "\$HOME/bin missing in \$PATH, adding it to a login configuration file."
    added=false
    for profile in "$HOME/.bash_profile" "$HOME/.bash_login" "$HOME/.profile" ; do
        if [ -f "$profile" ] && grep -q 'PATH=' "$profile" ; then
            sed -i 's|PATH="|PATH="$HOME/bin:|' "$profile"
            echo "Updated PATH in $profile"
            added=true
            break
        fi
    done
    if [ "$added" = false ] ; then
        echo "Couldn't find a login file with a PATH entry; add \$HOME/bin to"
        echo "your PATH manually. Bailing out..."
        exit 1
    fi
else
    echo "\$PATH already contains \$HOME/bin, no update needed"
fi

# ---------------------------------------------------------------------------
# Aliases: rewrite g, g+ and g- idempotently inside a managed sentinel block
# ---------------------------------------------------------------------------
write_managed_aliases new

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
if [ "$update" = false ] ; then
    echo "Installation completed."
    echo "Logout and login again (or 'source ~/.bash_aliases') to pick up aliases."
else
    echo "Update completed."
fi
exit 0
