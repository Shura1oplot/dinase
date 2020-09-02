#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import os
import urlparse
import logging

import trafaret as t

from dinase.feed import get_feed


def main(argv=sys.argv):  # pylint: disable=W0102,W0613
    logging.basicConfig(
        format="%(asctime)s : %(process)d : %(levelname)s : %(message)s",
        filename="/var/log/dinase.log",
        level=logging.WARNING
    )

    query = urlparse.parse_qsl(os.environ.get("QUERY_STRING", ""))
    args = t.Dict({
        t.Key("r"): t.String
    }).check(dict(query))

    sys.stdout.write("Content-type:application/atom+xml;charset=utf-8\n\n")
    sys.stdout.write(get_feed(args["r"]))
    sys.stdout.flush()


if __name__ == "__main__":
    sys.exit(main())
