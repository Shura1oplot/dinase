# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from . import url, html


def clean(entry):
    if "links" in entry:
        for link in entry["links"]:
            link["href"] = url.unproxy(link["href"])

    if "summary" in entry and entry["summary"]["type"] == "text/html":
        entry["summary"]["value"] = html.clean(entry["summary"]["value"])
