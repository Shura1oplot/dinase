#!/bin/sh

set -e

INSTALL_DIR=$HOME/tmp/dinase/cgi-bin/dinase

OWNER=root
GROUP=www-data

pyclean .

do_install() {
    for src in "$@"; do
        if [ -d "$src" ]; then
            dst=$INSTALL_DIR/$(basename "$src")
            cp -R "$src" "$dst"
            find "$dst" -exec chown $OWNER:$GROUP {} \;
            find "$dst" -type d -exec chmod 0755 {} \;
            find "$dst" -type f -exec chmod 0644 {} \;
        else
            if [ "$(head -c 2 "$src")" = "#!" ]; then
                mode=0755
            else
                mode=0644
            fi
            /usr/bin/install -o $OWNER -g $GROUP -m $mode -t "$INSTALL_DIR" "$src"
        fi
    done
}

mkdir -p "$INSTALL_DIR"
rm -rf "$INSTALL_DIR"/* || true

do_install dinase
do_install dinase.py
do_install cli.py
chmod 0644 "$INSTALL_DIR/cli.py"
# do_install newsgrabbers/*

# do_install pirate/*
