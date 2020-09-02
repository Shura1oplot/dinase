# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import trafaret as t

from dinase.sugar.func import identity, constantly, iffy


def trafaret(result=None):
    tree = t.Forward()

    tree.provide(
        t.Or(
            t.Dict({
                t.Key("condition"): t.String,
                t.Key("true"): tree,
                t.Key("false"): tree,
            }),
            t.Dict({
                t.Key("result"): result or t.Any
            }),
            t.Dict({
                t.Key("join"): t.String
            }),
        )
    )

    return tree


def compile(node, condition=identity, branches=None):  # pylint: disable=W0622
    branches = branches or {}

    if "result" in node:
        result = node["result"]
        return constantly(result)

    if "join" in node:
        name = node["join"]
        return compile(branches[name], condition, branches)

    return iffy(
        condition(node["condition"]),
        compile(node["true"], condition, branches),
        compile(node["false"], condition, branches)
    )
