# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import trafaret as t

from .utils import load_json


__all__ = ("feeds", )


feeds = t.Dict({
    t.String: t.Dict({
        t.Key("url"): t.String,
        t.Key("usertags", optional=True): t.List(t.String),
        t.Key("disable", default=False): t.Bool,
        t.Key("replace", optional=True): t.Dict({
            t.Key("title", optional=True): t.String,
            t.Key("subtitle", optional=True): t.String,
            t.Key("author", optional=True): t.Or(
                t.String,
                t.Dict({
                    t.Key("name",  optional=True): t.String,
                    t.Key("href",  optional=True): t.String,
                    t.Key("email", optional=True): t.String,
                })
            )
        })
    })
}).check(load_json("feeds.json"))
