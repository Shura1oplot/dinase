# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
from urlparse import urlparse, parse_qsl

from grab import Grab


feedsportal_replace = {
    "0A": "0", "0B": ".",       "0C": "/",        "0D": "?",    "0E": "-",
    "0F": "=", "0G": "&",       "0H": ",",        "0I": "_",    "0J": "%",
    "0K": "+", "0L": "http://", "0M": "https://", "0N": ".com", "0O": ".co.uk",
    "0P": ";", "0Q": "|",       "0R": ":",        "0S": "www.", "0T": "#",
    "0U": "$", "0V": "~",       "0W": "!",        "0X": "(",    "0Y": ")",
    "0Z": "Z"
}


def unproxy(url):
    try:
        parsed_url = urlparse(url)
    except ValueError:
        return url

    if not parsed_url:
        return url

    if not parsed_url.scheme and url.startswith("//"):
        url = "http:{}".format(url)

    netloc = parsed_url.netloc

    if netloc.endswith(".feedsportal.com"):
        match = re.match((r"http://[a-zA-Z0-0.]*\.feedsportal\.com/[/0-9a-z]*/"
                          r"(?P<url>[0-9a-zA-Z]+)/story[0-9]{2}\.html?"), url)

        if not match:
            return url

        parts = []

        for x in re.split(r"(0[A-Z])", match.group("url")):
            parts.append(feedsportal_replace.get(x, x))

        return unproxy("".join(parts))

    if netloc in ("feedproxy.google.com", "feeds.feedburner.com"):
        grab = Grab(follow_location=False, follow_refresh=False,
                    nobody=True, hammer_mode=True)
        grab.go(url)

        if grab.response.code not in (301, 302):
            return url

        if "Location" not in grab.response.headers:
            return url

        return unproxy(grab.response.headers["Location"])

    if netloc == "news.yandex.ru":
        params = dict(parse_qsl(parsed_url.query))

        cl4url = params.get("cl4url")

        if not cl4url:
            return url

        if not urlparse(cl4url).scheme:
            cl4url = "http://{}".format(cl4url)

        return unproxy(cl4url)

    return url
