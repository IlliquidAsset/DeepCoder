#!/bin/bash
# Quick installer for DeepCoder command

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BIN_DIR="$SCRIPT_DIR/bin"

if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$BIN_DIR/deepcoder" "/usr/local/bin/deepcoder"
    echo "DeepCoder command installed to /usr/local/bin"
elif [ -d "$HOME/.local/bin" ]; then
    mkdir -p "$HOME/.local/bin"
    ln -sf "$BIN_DIR/deepcoder" "$HOME/.local/bin/deepcoder"
    echo "DeepCoder command installed to $HOME/.local/bin"
else
    echo "Could not install to system directory. Use $BIN_DIR/deepcoder directly."
fi
