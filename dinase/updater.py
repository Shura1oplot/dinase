# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import multiprocessing

from dinase.sugar.func import unzip
from dinase.sugar.dict import iteritems, iterkeys
from dinase.sugar.exc import pickleble_exc_info, format_exception

from .config import PROCESS_COUNT, feeds
from .model import Heads, Entries
from .feedlib import parse


def update(names=None, callback=None):
    tasks = _select_tasks(names)

    for name, success, result in _get_feeds(tasks, PROCESS_COUNT):
        if success:
            head, entries = result
            Heads.save(head, name)
            info = Entries.save(entries, name)

        else:
            exc_type, exc_value, exc_traceback = result
            exc_msg_full = "".join(format_exception(exc_type, exc_value, exc_traceback))
            exc_msg_short = "".join(format_exception(exc_type, exc_value)).strip()
            logging.error("cannot get feed: {}".format(name))
            logging.debug(exc_msg_full)
            info = exc_msg_short

        if callback:
            callback(name, success, info)


def _select_tasks(names=None):
    if names is None:
        names = list(iterkeys(feeds))

    result = []

    for name, feed in iteritems(feeds):
        if name not in names or feed["disable"]:
            continue

        result.append((name, feed["url"]))

    return result


def _get_feeds(tasks, processes):
    pool = multiprocessing.Pool(processes=min(processes, len(tasks)))
    it = pool.imap_unordered(_get_feed, tasks)
    done = []

    try:
        while True:
            name, success, result = it.next(timeout=90)
            done.append(name)
            yield name, success, result

    except multiprocessing.TimeoutError:
        names, _ = unzip(tasks)
        undone = [name for name in names if name not in done]
        logging.error("updater timeout: {}".format(", ".join(undone)))

    finally:
        pool.terminate()
        pool.join()


def _get_feed(task):
    try:
        feed_name, url = task
        feed, entries = parse(url)
        return (feed_name, True, (feed, entries))
    except Exception:  # pylint: disable=W0703
        return (feed_name, False, pickleble_exc_info())
