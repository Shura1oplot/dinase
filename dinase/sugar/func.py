# -*- coding: utf-8 -*-

from operator import __not__
from itertools import starmap
from inspect import getargspec, getcallargs

from .future import *  # pylint: disable=W0622,W0401,W0614


def isnone(obj):
    return obj is None


def notnone(obj):
    return obj is not None


def identity(obj):
    return obj


def constantly(value):
    return lambda *args, **kwargs: value


def caller(*args, **kwargs):
    return lambda function: function(*args, **kwargs)


def star(function):
    return lambda args: function(*args)


def dstar(function):
    return lambda kwargs: function(**kwargs)


def compose(*functions):
    return reduce(
        lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)),
        reversed(functions)
    )


def complement(function):
    return compose(function, __not__)


def unzip(zipped):
    return zip(*zipped)


def zipwith(function):
    return lambda *iterables: starmap(function, zip(*iterables))


def keep(function, *iterables):
    return filter(None, map(function, *iterables))


def juxt(*functions):
    return lambda *args, **kwargs: \
        (function(*args, **kwargs) for function in functions)


def iffy(predicate, action=None, default=None):
    if action is None:
        predicate, action, default = bool, predicate, default

    if not callable(default):
        default = constantly(default)

    def func(value):
        if predicate(value):
            return action(value)
        return default(value)

    return func


def classname(obj):
    return obj.__class__.__name__


def raiser(exception, *args, **kwargs):
    if isinstance(exception, type):
        exception = exception(*args, **kwargs)

    def func(*args, **kwargs):  # pylint: disable=W0613
        raise exception

    return func


def curry(function):
    argnames, varargs, keywords, defaults = getargspec(function)

    if not argnames:
        raise ValueError("function without arguments is unsupported")

    if varargs or keywords:
        raise ValueError("function with variable count of arguments is unsupported")

    if defaults:
        raise ValueError("function with default arguments is unsupported")

    argcount = len(argnames)
    args = []

    def func(arg):
        args.append(arg)
        if len(args) == argcount:
            return function(*args)
        return func

    return func


def papply(function, *args, **kwargs):

    fargs = list(args)
    fkwargs = kwargs

    def func(*args, **kwargs):
        fargs.extend(args)
        fkwargs.update(kwargs)

        try:
            getcallargs(function, *fargs, **fkwargs)
        except TypeError:
            return func
        return function(*fargs, **fkwargs)

    return func(*args, **kwargs)
