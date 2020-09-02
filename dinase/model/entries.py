# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from copy import copy

import pymongo

from .database import database
from .heads import Heads
from ..config import rubrics
from ..feedlib import fix_entry, content


class Entries(object):

    _entries = database["entries"]

    @classmethod
    def save(cls, entries, feed):
        def compare(a, b):
            def f(d):
                return {k: v for k, v in d.items() if not k.startswith("_")}

            return b is not None and f(a) == f(b)

        count = 0

        for entry in reversed(copy(entries)):
            query = {}

            for key in ("id", "link"):
                if key in entry:
                    query[key] = entry[key]

            if not query:
                continue

            query["_feed"] = feed
            similar_entry = cls._entries.find_one(query)

            if compare(entry, similar_entry):
                continue

            entry["_feed"] = feed
            entry["_rubrics"] = {"include": [], "exclude": []}
            entry["_valid"] = True
            entry["_fixed"] = None

            if similar_entry:
                entry["_id"] = similar_entry["_id"]
                entry["_added"] = similar_entry["_added"]

            else:
                entry["_added"] = datetime.datetime.today()
                count += 1

            cls._entries.save(entry, safe=True)

        cls._entries.ensure_index("_added")

        return count

    @classmethod
    def select(cls, rubric, fields=None):
        rule = rubrics[rubric]["rule"]
        cache = rubrics[rubric]["cache"]
        head = Heads.get(rubric)
        query = {"_rubrics.exclude": {"$ne": rubric}, "_valid": True}

        entries = cls._entries.find(query, fields=fields).sort(
            "_added", direction=pymongo.DESCENDING)

        for entry in entries:
            fixed_entry = entry["_fixed"]

            if not fixed_entry:
                fixed_entry = fix_entry(entry, head)

                if fixed_entry:
                    fixed_entry["_feed"] = entry["_feed"]
                    fixed_entry["_added"] = entry["_added"]
                    fixed_entry["id"] = "urn:dinase:{}".format(entry["_id"])
                    content.clean(fixed_entry)

                cls._entries.update({"_id": entry["_id"]},
                                    {"$set": {"_valid": bool(fixed_entry),
                                              "_fixed": fixed_entry or None}},
                                    upsert=False, safe=True)

            if not fixed_entry:
                continue

            if rubric in entry["_rubrics"]["include"]:
                yield fixed_entry
                continue

            section = "include" if rule(fixed_entry) else "exclude"

            if cache:
                cls._entries.update(
                    {"_id": entry["_id"]},
                    {"$push": {"_rubrics.{}".format(section): rubric}},
                    upsert=False, safe=True,
                )

            if section == "include":
                yield fixed_entry

    @classmethod
    def remove(cls, rubric):
        for entry in list(cls.select(rubric, fields=["_id", ])):
            cls._entries.remove(entry["_id"], safe=True)

    @classmethod
    def purge_cache(cls):
        cls._entries.update(
            {}, {"$set": {"_rubrics": {"include": [], "exclude": []},
                          "_valid": True,
                          "_fixed": None}},
            upsert=False, multi=True, safe=True
        )
