# -*- coding: utf-8 -*-

from .future import *  # pylint: disable=W0622,W0401,W0614


if PY2:
    def iterkeys(dictonary):
        try:
            return dictonary.iterkeys()
        except AttributeError:
            return iter(dictonary.keys())

    def itervalues(dictonary):
        try:
            return dictonary.itervalues()
        except AttributeError:
            return iter(dictonary.values())

    def iteritems(dictonary):
        try:
            return dictonary.iteritems()
        except AttributeError:
            return iter(dictonary.items())

else:
    def iterkeys(dictonary):
        return iter(dictonary.keys())

    def itervalues(dictonary):
        return iter(dictonary.values())

    def iteritems(dictonary):
        return iter(dictonary.items())


def zipdict(keys, values):
    return dict(zip(keys, values))


def unzipdict(dictonary):
    return iterkeys(dictonary), itervalues(dictonary)


def map_dict(function, dictonary):
    return dict(map(function, *unzipdict(dictonary)))


def map_keys(function, dictonary):
    keys, values = unzipdict(dictonary)
    return zipdict(map(function, keys), values)


def map_values(function, dictonary):
    keys, values = unzipdict(dictonary)
    return zipdict(keys, map(function, values))


def filter_dict(function, dictonary):
    return {k: v for k, v in iteritems(dictonary)
            if function(k, v)}


def filter_keys(function, dictonary):
    return {k: v for k, v in iteritems(dictonary)
            if function(k)}


def filter_values(function, dictonary):
    return {k: v for k, v in iteritems(dictonary)
            if function(v)}


def compact_dict(dictonary):
    return {k: v for k, v in iteritems(dictonary)
            if v is not None}


def project(dictonary, keys):
    return {k: v for k, v in iteritems(dictonary)
            if k in keys}


def where(dictonaries, **conditions):
    return (dct for dct in dictonaries
            if all(dct[k] == v for k, v in iteritems(conditions)))


def pluck(key, dictonaries):
    return (dct.get(key) for dct in dictonaries)


def merge(*dictonaries):
    result = {}

    for dictonary in dictonaries:
        result.update(dictonary)

    return result


def deep_merge(*dictonaries):
    result = {}

    for dictonary in dictonaries:
        for key, value in iteritems(dictonary):
            if key in result and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value

    return result
