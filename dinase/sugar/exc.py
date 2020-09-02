# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
import traceback

from .future import *  # pylint: disable=W0622,W0401,W0614


def pickleble_exc_info():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    sys.exc_clear()
    return exc_type, exc_value, traceback.extract_tb(exc_traceback)


def format_extracted_traceback(exc_extracted_traceback):
    result = ["Traceback (most recent call last):\n", ]

    for tb in exc_extracted_traceback:
        result.append("  File \"{0}\", line {1}, in {2}\n".format(*tb))
        result.append("    {3}\n".format(*tb))

    return result


def format_exception(exc_type, exc_value=None, exc_extracted_traceback=None):
    if isinstance(exc_type, tuple) and len(exc_type) == 3:
        exc_type, exc_value, exc_extracted_traceback = exc_type

    result = []

    if exc_extracted_traceback:
        result += format_extracted_traceback(exc_extracted_traceback)

    result += traceback.format_exception_only(exc_type, exc_value)

    return result
