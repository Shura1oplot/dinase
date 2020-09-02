# -*- coding: utf-8 -*-

import os


DATABASE = {
    "NAME": "dinase",
    "HOST": "127.0.0.1",
    "PORT": 27017,
    "USERNAME": "",
    "PASSWORD": ""
}

LINK_MASK = "http://dinase.dyndns.org/cgi-bin/dinase/dinase.py?r={rubric}"

JSON_DIR = os.path.dirname(__file__)

PROCESS_COUNT = 10
