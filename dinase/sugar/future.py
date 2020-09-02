# -*- coding: utf-8 -*-

# pylint: disable=W0611,W0622,E0611,F0401

import sys


__all__ = []


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
__all__.extend(("PY2", "PY3"))


# types
if PY2:
    import types
    string_types = basestring,
    integer_types = (int, long)
    default_integer_type = long
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

else:
    string_types = (str,)
    integer_types = (int,)
    default_integer_type = int
    class_types = (type,)
    text_type = str
    binary_type = bytes

__all__.extend(("string_types",
                "integer_types",
                "default_integer_type",
                "class_types",
                "text_type",
                "binary_type"))


# unicode, unichr
if PY2:
    from __builtin__ import unicode, unichr

else:
    from builtins import (
        str as unicode,
        chr as unichr,
    )
    __all__.extend(("unicode", "unichr"))


# cmp
if PY2:
    from __builtin__ import cmp

else:
    def cmp(x, y):
        return (x > y) - (x < y)
    __all__.append("cmp")


# input
if PY2:
    from __builtin__ import raw_input as input
    __all__.append("input")

else:
    from builtins import input


# open
if PY2:
    from io import open
    __all__.append("open")

else:
    from builtins import open


# ascii, oct, hex
if PY2:
    from future_builtins import ascii, oct, hex
    __all__.extend(("ascii", "oct", "hex"))

else:
    from builtins import ascii, oct, hex


# range
if PY2:
    from __builtin__ import xrange as range
    __all__.append("range")

else:
    from builtins import range


# reload
if PY2:
    from __builtin__ import reload

else:
    from imp import reload
    __all__.append("reload")


# map, filter, zip
if PY2:
    try:
        from future_builtins import map, filter, zip
    except ImportError:
        from itertools import (
            imap as map,
            ifilter as filter,
            izip as zip,
        )
    __all__.extend(("map", "filter", "zip"))

else:
    from builtins import map, filter, zip


# filterfalse, zip_longest
if PY2:
    from itertools import (
        ifilterfalse as filterfalse,
        izip_longest as zip_longest,
    )

else:
    from itertools import filterfalse, zip_longest

__all__.extend(("filterfalse", "zip_longest"))


# reduce
if PY2:
    from __builtin__ import reduce

else:
    from functools import reduce
    __all__.append("reduce")


# __str__, __unicode__
if PY2:
    def unicode_compatible(cls):
        setattr(cls, "__unicode__", cls.__str__)

        def __str__(self):
            return self.__unicode__().encode("utf-8")

        setattr(cls, "__str__", __str__)

else:
    def unicode_compatible(cls):
        return cls

__all__.append("unicode_compatible")
