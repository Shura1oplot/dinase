# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import trafaret as t

from dinase.logiclib.predicates import PredicateCompiler
from dinase.sugar.dict import iteritems

from .filters import filters
from .utils import load_json


__all__ = ("rubrics", )


class Rule(object):

    _compile = PredicateCompiler(filters).compile

    def __init__(self, source):
        super(Rule, self).__init__()

        self._source = source

    def __call__(self, *args, **kwargs):  # pylint: disable=E0202
        rule = self.__call__ = self._compile(self._source)

        return rule(*args, **kwargs)


class Rubrics(dict):
    def __init__(self, *args, **kwargs):
        super(Rubrics, self).__init__(*args, **kwargs)

        for name, rubric in iteritems(self):
            rubric["name"] = name
            rubric["rule"] = Rule(rubric["rule"])

    def __missing__(self, key):  # pylint: disable=R0201
        exc_text = "rubric '{}' not found".format(key)
        logging.error(exc_text)
        raise KeyError(exc_text)


rubrics = Rubrics(t.Dict({
    t.String: t.Dict({
        t.Key("rule"): t.String,
        t.Key("length", default=100): t.Int(gt=0),
        t.Key("template"): t.Dict({
            t.Key("title"): t.String,
            t.Key("subtitle", optional=True): t.String,
            t.Key("links", optional=True): t.List(t.String),
            t.Key("author", optional=True): t.Dict({
                t.Key("name"): t.String,
                t.Key("url", optional=True): t.String,
                t.Key("email", optional=True): t.String
            })
        }),
        t.Key("no_authors", default=True): t.Bool,
        t.Key("cache", default=True): t.Bool
    })
}).check(load_json("rubrics.json")))
