# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import feedparser
from grab import Grab

from .fixer import fix_head, fix_entries


def parse(url):
    grab = Grab(hammer_mode=True)
    grab.go(url)

    body = grab.response.unicode_body()
    feed = feedparser.parse(body)

    head = feed.get("feed")

    if not head:
        raise IOError("feed without head")

    head = fix_head(head)

    if not head:
        raise IOError("invalid head, cannot fix")

    entries = fix_entries(feed.get("entries"), head)

    return head, entries
