#!/bin/sh

for grabber in newsgrabbers/*.py ; do
    if [ "$(head -c 2 "$grabber")" != "#!" ]; then
        continue
    fi
    python "$grabber" >/dev/null 2>&1
    echo "$grabber: $?"
done
