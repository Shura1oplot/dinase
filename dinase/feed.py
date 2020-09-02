# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from dinase.sugar.dict import iteritems

from .config import LINK_MASK, rubrics
from .model import Heads, Entries
from .feedlib import get_atom, fix_head


def get_feed(rubric):
    rubric_name = rubric
    rubric = rubrics[rubric_name]

    heads = {}
    entries = []
    length = rubric["length"]
    no_authors = rubric["no_authors"]

    for entry in Entries.select(rubric_name):
        feed = entry["_feed"]

        if feed in heads:
            head = heads[feed]

        else:
            head = Heads.get(feed)

            if head is None:
                continue

            heads[feed] = head

        if no_authors:
            if "title" in head:
                entry["author"] = {
                    "name": head["title"]["value"],
                }

            elif "author" in entry:
                del entry["author"]

        entry = {key: value for key, value in iteritems(entry)
                 if not key.startswith("_")}

        entries.append(entry)

        if len(entries) == length:
            break

    head = _generate_head(rubric)
    return get_atom(head, entries)


def _generate_head(rubric):
    template = rubric["template"]
    link = LINK_MASK.format(rubric=rubric["name"])

    head = {
        "title": {
            "value": template["title"],
            "type": "text/plain"
        }
    }

    if "subtitle" in template:
        head["subtitle"] = {
            "value": template["subtitle"],
            "type": "text/plain"
        }

    head["link"] = link

    head["links"] = [
        {
            "rel":  "self",
            "href": link,
            "type": "application/atom+xml"
        }
    ]

    if "links" in template:
        for href in template["links"]:
            head["links"].append({
                "rel":  "alternate",
                "href": href
            })

    if "author" in template:
        head["author"] = template["author"]

    # TODO: add atom field rubrics
    # TODO: add atom field generator

    return fix_head(head)
