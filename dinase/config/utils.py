# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import codecs
import json

from .settings import JSON_DIR


def load_json(fname):
    fp = codecs.open(os.path.join(JSON_DIR, fname), "r", encoding="utf-8")
    lines = (line for line in fp if not line.lstrip().startswith("//"))
    return json.loads("".join(lines))
