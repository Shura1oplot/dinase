# -*- coding: utf-8 -*-

from collections import Iterable, Iterator, defaultdict
from functools import partial

from .func import identity, notnone
from .future import *  # pylint: disable=W0622,W0401,W0614


def factory(collection):
    if isinstance(collection, defaultdict):
        return partial(defaultdict, collection.default_factory)

    if isinstance(collection, Iterator):
        return identity

    if isinstance(collection, string_types):
        return collection.__class__().join

    return collection.__class__


def new(collection, *args, **kwargs):
    return factory(collection)(*args, **kwargs)


def isiterable(collection):
    return isinstance(collection, Iterable)


def isempty(collection):
    try:
        next(iter(collection))
    except StopIteration:
        return True
    else:
        return False


def enum_members(start=1):
    i = start
    while True:
        yield i
        i += 1


def compact(collection):
    return new(collection, filter(notnone, collection))
