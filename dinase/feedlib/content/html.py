# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import lxml.html
from grab.tools.lxml_tools import clean_html


crap_xpaths = [
    "//div[@class='mf-related']",
    "//div[@class='mf-viral']"
]


_crap_urls = (
    "feedsportal.com",
    "feeds.feedburner.com",
    "feedproxy.google.com",
)
_crap_xpath_templates = (
    "//img[contains(@src, '{}/')]",
    "//a[contains(@href, '{}/')]",
)
for url in _crap_urls:
    for template in _crap_xpath_templates:
        crap_xpaths.append(template.format(url))


def clean(html):
    tree = lxml.html.fromstring(html)

    for xpath in crap_xpaths:
        for elem in tree.xpath(xpath):
            elem.getparent().remove(elem)

    html = lxml.html.tostring(tree, encoding="unicode")

    return clean_html(html)
