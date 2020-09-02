# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import traceback
import pymongo

from ..config import DATABASE


__all__ = ("database", "drop")


try:
    _connection = pymongo.Connection(
        DATABASE["HOST"],
        DATABASE["PORT"],
    )
except pymongo.errors.ConnectionFailure:
    exception = "".join(traceback.format_exc())
    logging.critical("cannot connect to mongodb server")
    logging.debug(exception)
    raise

# TODO: impl auth

database = _connection[DATABASE["NAME"]]


def drop():
    database.drop_collection("heads")
    database.drop_collection("entries")
