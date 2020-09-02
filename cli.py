#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import logging
import argparse

import unixfilelock

from dinase import __version__


def main(argv=sys.argv):  # pylint: disable=W0102
    parser = argparse.ArgumentParser(
        prog=os.path.basename(argv[0]),
        description="Dinase v{}".format(__version__),
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s v{}".format(__version__),
    )
    parser.add_argument(
        "-u", "--update-all",
        action="store_true",
        help="Update all feeds",
    )
    parser.add_argument(
        "-r", "--rubric",
        type=str,
        metavar="NAME",
        help="Select rubric",
    )
    parser.add_argument(
        "-d", "--delete",
        action="store_true",
        help=("Delete all entries from selected rubric. "
              "If rubric is not specified, it deletes all entries from database."),
    )
    parser.add_argument(
        "-n", "--no-log",
        action="store_true",
        help="Disable logging",
    )
    parser.add_argument(
        "-p", "--purge-cache",
        action="store_true",
        help="Purge rubrics cache",
    )
    args = parser.parse_args(argv[1:])

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s : %(process)d : %(levelname)s : %(message)s",
        filename="/dev/null" if args.no_log else "/var/log/dinase.log",
    )

    if args.update_all or args.delete or args.purge_cache:
        lock = unixfilelock.UnixFileLock("/run/lock/dinase.lock")

        try:
            lock.acquire()
        except unixfilelock.AlreadyLocked:
            print("{}: locked by other process".format(argv[0]))
            return 0

        if args.purge_cache:
            from dinase.model import Entries
            Entries.purge_cache()

        if args.delete:
            if args.rubric:
                from dinase.model import Entries
                Entries.remove(args.rubric)

            else:
                from dinase.model import drop
                drop()

        if args.update_all:
            from dinase.updater import update

            def on_feed_updated(name, success, info):  # pylint: disable=W0613
                print("{}: {}".format(name, info))

            update(callback=on_feed_updated)

        lock.release()

    if args.rubric and not args.delete:
        from dinase.feed import get_feed
        sys.stdout.write(get_feed(args.rubric))
        sys.stdout.flush()


if __name__ == "__main__":
    sys.exit(main())
