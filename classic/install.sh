#!/bin/bash
#
# Copyright (C) Torbjorn Hedqvist - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT license. See LICENSE file in the project
# root for full license information.

# Check the prerequisites
if [ -z "$HOME" ] ; then
    echo "\$HOME not set which is required for installation to work properly."
    echo "Bailing out..."
    exit 1
else
    echo "All prerequisites are OK, let's start the installation."
fi

# Managed environment support. If $HOME/.bashrc.user exists, ~/.bashrc and the
# login files must not be modified; ~/.bashrc.user is the place for private
# settings. ~/.bash_aliases is still used for the aliases, but ~/.bashrc.user
# then gets one small marked block that sources it and puts ~/bin on PATH.
# FCD_RC_FILE=<file> selects another private rc file instead.
RC_USER_FILE="${FCD_RC_FILE:-$HOME/.bashrc.user}"
if [ -n "${FCD_RC_FILE:-}" ] || [ -f "$RC_USER_FILE" ] ; then
    managed_env=true
    echo "Managed environment: $RC_USER_FILE will be used instead of modifying login files."
else
    managed_env=false
fi

# Make the private rc file source ~/.bash_aliases and put ~/bin on PATH.
# Idempotent: only the block between the markers is ever replaced.
ensure_rc_hook() {
    local rc="$RC_USER_FILE"
    [ -f "$rc" ] || echo "# File created by fcd installation script" > "$rc"
    if grep -q '# >>> fcd hook >>>' "$rc" ; then
        sed -i '/# >>> fcd hook >>>/,/# <<< fcd hook <<</d' "$rc"
    fi
    {
        echo ""
        echo "# >>> fcd hook >>>"
        echo "# Managed by fcd install.sh - safe to regenerate."
        # Don't source it twice if the user's own lines already do.
        if ! grep -q 'bash_aliases' "$rc" ; then
            echo '[ -f "$HOME/.bash_aliases" ] && . "$HOME/.bash_aliases"'
        fi
        echo 'case ":$PATH:" in *":$HOME/bin:"*) ;; *) export PATH="$HOME/bin:$PATH" ;; esac'
        echo "# <<< fcd hook <<<"
    } >> "$rc"
    echo "Updated the fcd block in $rc"
}

# Fresh install or updating
update=false

if [ ! -d $HOME/bin ] ; then
    echo "Creating $HOME/bin directory"
    mkdir $HOME/bin
    if [ $? -ne 0 ] ; then
        echo "Failed to create $HOME/bin directory. Can't continue."
        echo "Bailing out..."
        exit 1
    fi
else
    echo "User already has a $HOME/bin directory, no need to create."
fi


# Check if the home bin directory is writable
if [ ! -w $HOME/bin ] ; then
    # It's not, try to fix that
    chmod u+w $HOME/bin
    if $? -ne 0 ] ; then
        echo "Failed to make $HOME/bin writable. Can't continue."
        echo "Bailing out..."
        exit 1
    fi
else
    echo "$HOME/bin is writable."
fi

# Check if this is first install or update or re-install
if [ -e $HOME/bin/fcd.py ] ; then
    echo "Seems you have an old installation, replace with new installation."
    update=true
fi

# Copying all needed files
echo "Copying the fcd files to $HOME/bin."
cp ./fcd.py $HOME/bin
cp ./fcd.sh $HOME/bin
cp ./README.md $HOME/bin/fcd-README.md
cp ./LICENSE $HOME/bin/fcd-LICENSE

echo "Making the scripts executable."
chmod u+x $HOME/bin/fcd.*

echo "And making sure the fcd-README.md and fcd-LICENSE files are not."
chmod ugo-x $HOME/bin/fcd-README.md
chmod ugo-x $HOME/bin/fcd-LICENSE
echo "ls -l $HOME/bin"
ls -l $HOME/bin

# Check if the user has the $HOME/bin directory included in the $PATH
# If not, update the appropriate login configuration file
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "\$HOME/bin missing in \$PATH, adding it to appropriate configuration file."
    if [ "$managed_env" = true ] ; then
        # Managed environment: leave the login files alone. PATH is extended
        # from the private rc file (see ensure_rc_hook below).
        echo "PATH will be extended from $RC_USER_FILE."
    elif [ -f $HOME/.bash_profile ] ; then
        echo "Found a $HOME/.bash_profile file."
        cat $HOME/.bash_profile |grep PATH= &>/dev/null
        if [ $? -eq 0 ] ; then
            echo "And it has a PATH, prepend it with \$HOME/bin"
            sed -i 's|PATH="|PATH="$HOME/bin:|' $HOME/.bash_profile
        else
            echo "Doesn't contain a PATH, can't continue."
            echo "Bailing out..."
            exit 1
        fi
    elif [ -f $HOME/.bash_login ] ; then
        echo "Found a $HOME/.bash_login file."
        cat $HOME/.bash_login |grep PATH= &>/dev/null
        if [ $? -eq 0 ] ; then
            echo "And it has a PATH, prepend it with \$HOME/bin"
            sed -i 's|PATH="|PATH="$HOME/bin:|' $HOME/.bash_login
        else
            echo "Doesn't contain a PATH, can't continue."
            echo "Bailing out..."
            exit 1
        fi
    elif [ -f $HOME/.profile ] ; then
        echo "Found a $HOME/.profile file."
        cat $HOME/.profile |grep PATH= &>/dev/null
        if [ $? -eq 0 ] ; then
            echo "And it has a PATH, prepend it with \$HOME/bin"
            sed -i 's|PATH="|PATH="$HOME/bin:|' $HOME/.profile
        else
            echo "Doesn't contain a PATH, can't continue."
            echo "Bailing out..."
            exit 1
        fi
    else
        echo "Couldn't find a valid configuration file in the users \$HOME."
        echo "Bailing out..."
        exit 1
    fi
else
    echo "\$PATH already contains \$HOME/bin, no update needed"
fi

# Check if the user has a .bash_aliases file in home, if not create it
# and insert the needed aliases into .bash_aliases
if [ ! -f $HOME/.bash_aliases ] ; then
    echo "User has no $HOME/.bash_aliases file, creating it."
    echo "# File created by fcd installation script" > $HOME/.bash_aliases
    echo "" >> $HOME/.bash_aliases
else
    echo "$HOME/.bash_aliases already exists."
fi

cat $HOME/.bash_aliases | grep "alias g+=" &>/dev/null
if [ $? -ne 0 ] ; then
    echo "Adding the g+ alias."
    echo "# Aliases created by fcd installation script" >> $HOME/.bash_aliases
    echo "alias g+='fcd.py -a \"\$@\"'" >> $HOME/.bash_aliases
else
    if [[ "$update" == "false" ]] ; then
        echo "Seems g+ alias is already set. Please create your own aliases."
        echo "Bailing out..."
        exit 1
    fi
fi

cat $HOME/.bash_aliases | grep "alias g-=" &>/dev/null
if [ $? -ne 0 ] ; then
    echo "Adding the g- alias."
    echo "alias g-='fcd.py -d \"\$@\"'" >> $HOME/.bash_aliases
else
    if [[ "$update" == "false" ]] ; then
        echo "Seems g- alias is already set. Please create your own aliases."
        echo "Bailing out..."
        exit 1
    fi
fi

cat $HOME/.bash_aliases | grep "alias g=" &>/dev/null
if [ $? -ne 0 ] ; then
    echo "Adding the g alias."
    echo "alias g='source ~/bin/fcd.sh \"\$@\"'" >> $HOME/.bash_aliases
    echo " " >> $HOME/.bash_aliases
else
    if [[ "$update" == "false" ]] ; then
        echo "Seems g alias is already set. Please create your own aliases."
        echo "Bailing out..."
        exit 1
    fi
fi

# In a managed environment, make sure the private rc file loads the aliases
# and puts ~/bin on PATH.
if [ "$managed_env" = true ] ; then
    ensure_rc_hook
fi

# Done
if [[ "$update" == "false" ]] ; then
    echo "Installation completed."
    echo "Logout and login again to ensure proper \$PATH and aliases updates"
else
    echo "Update completed, no change to PATH or aliases"
fi
exit 0
