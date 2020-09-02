# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from .database import database
from ..config import feeds


class Heads(object):

    _heads = database["heads"]

    @classmethod
    def save(cls, head, feed):
        replace = feeds[feed].get("replace")

        if replace:
            for key in ("title", "subtitle"):
                if key in replace:
                    head[key] = {
                        "value": replace[key],
                        "type": "text/plain"
                    }

            if "author" in replace:
                author = replace["author"]

                if isinstance(author, dict):
                    head["author"] = author

                else:
                    if "author" in head:
                        head["author"] = {}

                    head["author"]["name"] = author

        head["_feed"] = feed
        cls._heads.find_and_modify({"_feed": feed}, head, new=True, upsert=True)
        cls._heads.ensure_index("_feed")

    @classmethod
    def get(cls, feed):
        return cls._heads.find_one({"_feed": feed})
