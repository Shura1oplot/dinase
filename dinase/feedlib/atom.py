# -*- coding: utf-8 -*-

# http://www.ietf.org/rfc/rfc4287.txt
# http://feedvalidator.org/

from __future__ import unicode_literals

import copy
import re

from lxml import etree

from dinase.sugar.dict import iteritems

from .. import datelib


__all__ = ("get_xml", )


def atomUri(uri):
    """
    atomUri = text
    """
    return uri


def atomEmailAddress(email):
    """
    atomEmailAddress = xsd:string { pattern = ".+@.+" }
    """
    if not re.match(r"^.+@.+$", email):
        raise ValueError("wrong email: {}".format(email))

    return email


def atomLanguageTag(lang):
    """
    atomLanguageTag = xsd:string {
        pattern = "[A-Za-z]{1,8}(-[A-Za-z0-9]{1,8})*"
    }
    """
    if not re.match(r"^[A-Za-z]{1,8}(-[A-Za-z0-9]{1,8})*$", lang):
        raise ValueError("wrong lang: {}".format(lang))

    return lang


def undefinedAttribute(value):
    """
    undefinedAttribute =
        attribute * - (xml:base | xml:lang | local:*) { text }
    """
    return value


def atomCommonAttributes(xml, attributes=None, skip=()):
    """
    atomCommonAttributes =
        attribute xml:base { atomUri }?,
        attribute xml:lang { atomLanguageTag }?,
        undefinedAttribute*
    """
    if not attributes:
        return

    for name, value in iteritems(attributes):
        if name in skip:
            continue

        if name == "base":
            xml.attrib["base"] = atomUri(value)

        elif name == "lang":
            xml.attrib["lang"] = atomLanguageTag(value)

        else:
            xml.attrib[name] = undefinedAttribute(value)


def atomPlainTextConstruct(xml, text, attributes=None):
    """
    atomPlainTextConstruct =
        atomCommonAttributes,
        attribute type { "text" | "html" }?,
        text
    """
    atomCommonAttributes(xml, attributes, skip=("type", ))

    if attributes and "type" in attributes:
        type_ = attributes["type"]

        if type_ != "html" and type_ != "text":
            raise ValueError("wrong type: {}".format(type_))

        xml.attrib["type"] = type_

    xml.text = text


def xhtmlDiv(xml, text, attributes=None):  # pylint: disable=W0613
    """
    xhtmlDiv = element xhtml:div {
        (attribute * { text }
         | text
         | anyXHTML)*
    }

    anyXHTML = element xhtml:* {
        (attribute * { text }
         | text
         | anyXHTML)*
    }
    """
    raise NotImplementedError("xhtml not supported")


def atomXHTMLTextConstruct(xml, xhtml, attributes):  # pylint: disable=W0613
    """
    atomXHTMLTextConstruct =
        atomCommonAttributes,
        attribute type { "xhtml" },
        xhtmlDiv
    """
    raise NotImplementedError("xhtml not supported")


def atomTextConstruct(xml, obj, attributes):
    """
    atomTextConstruct = atomPlainTextConstruct | atomXHTMLTextConstruct
    """
    if attributes["type"] == "xhtml":
        atomXHTMLTextConstruct(xml, obj, attributes)

    else:
        atomPlainTextConstruct(xml, obj, attributes)


def atomPersonConstruct(xml, elements, attributes=None):
    """
    atomPersonConstruct =
        atomCommonAttributes,
        (element atom:name { text }
         & element atom:uri { atomUri }?
         & element atom:email { atomEmailAddress }?
         & extensionElement*)

    extensionElement =
        simpleExtensionElement | structuredExtensionElement

    simpleExtensionElement =
        element * - atom:* {
            text
        }

    structuredExtensionElement =
        element * - atom:* {
                (attribute * { text }+,
                    (text|anyElement)*)
                 | (attribute * { text }*,
                    (text?, anyElement+, (text|anyElement)*))
        }

    anyElement =
        element * {
            (attribute * { text }
             | text
             | anyElement)*
        }
    """
    atomCommonAttributes(xml, attributes)
    if "name" in elements:
        etree.SubElement(xml, "name").text = elements["name"]

    if "uri" in elements:
        etree.SubElement(xml, "uri").text = atomUri(elements["uri"])

    if "email" in elements:
        etree.SubElement(xml, "email").text = atomEmailAddress(elements["email"])

    # NOTE: only simpleExtensionElement is supported
    for name, value in iteritems(elements):
        if name not in ("name", "uri", "email"):
            etree.SubElement(xml, name).text = value


def atomDateConstruct(xml, dateTime, attributes=None):
    """
    atomDateConstruct =
        atomCommonAttributes,
        xsd:dateTime
    """
    if not datelib.xsd.validate(dateTime):
        raise ValueError("wrong dateTime: {}".format(dateTime))

    atomCommonAttributes(xml, attributes)
    xml.text = dateTime


def atomInlineTextContent(xml, text, attributes=None):
    """
    atomInlineTextContent =
        element atom:content {
            atomCommonAttributes,
            attribute type { "text" | "html" }?,
            (text)*
        }
    """
    content = etree.SubElement(xml, "content")
    atomCommonAttributes(content, attributes, skip=("type", ))

    if attributes and "type" in attributes:
        type_ = attributes["type"]

        if type_ not in ("text", "html"):
            raise ValueError("wrong type: {}".format(type_))

        content.attrib["type"] = type_

    content.text = text


def atomInlineXHTMLContent(xml, xhtml, attributes):  # pylint: disable=W0613
    """
    atomInlineXHTMLContent =
        element atom:content {
            atomCommonAttributes,
            attribute type { "xhtml" },
            xhtmlDiv
        }
    """
    raise NotImplementedError("xhtml not supported")


def atomMediaType(media_type):
    """
    atomMediaType = xsd:string { pattern = ".+/.+" }
    """
    if not re.match(r"^.+/.+$", media_type):
        raise ValueError("wrong media type: {}".format(media_type))

    return media_type


def atomInlineOtherContent(xml, text, attributes=None):
    """
    atomInlineOtherContent =
        element atom:content {
            atomCommonAttributes,
            attribute type { atomMediaType }?,
            (text|anyElement)*
        }
    """
    content = etree.SubElement(xml, "content")
    atomCommonAttributes(content, attributes, skip=("type", ))

    if "type" in attributes:
        content.attrib["type"] = atomMediaType(attributes["type"])

    content.text = text  # NOTE: text only


def atomOutOfLineContent(xml, attributes):
    """
    atomOutOfLineContent =
        element atom:content {
            atomCommonAttributes,
            attribute type { atomMediaType }?,
            attribute src { atomUri },
            empty
        }
    """
    content = etree.SubElement(xml, "content")
    atomCommonAttributes(content, attributes, skip=("type", "src"))

    if "type" in attributes:
        content.attrib["type"] = atomMediaType(attributes["type"])

    content.attrib["src"] = atomUri(attributes["src"])


def atomContent(xml, obj=None, attributes=None):
    """
    atomContent = atomInlineTextContent
     | atomInlineXHTMLContent
     | atomInlineOtherContent
     | atomOutOfLineContent
    """
    if "type" in attributes:
        if attributes["type"] == "xhtml":
            atomInlineXHTMLContent(xml, obj, attributes)
        else:
            atomInlineTextContent(xml, obj, attributes)

    else:
        if obj:
            atomInlineOtherContent(xml, obj, attributes)
        else:
            atomOutOfLineContent(xml, attributes)


def atomAuthor(xml, elements, attributes=None):
    """
    atomAuthor = element atom:author { atomPersonConstruct }
    """
    author = etree.SubElement(xml, "author")
    atomPersonConstruct(author, elements, attributes)


def atomCategory(xml, text, attributes):
    """
    atomCategory =
        element atom:category {
            atomCommonAttributes,
            attribute term { text },
            attribute scheme { atomUri }?,
            attribute label { text }?,
            undefinedContent
        }

    undefinedContent = (text|anyForeignElement)*

    anyForeignElement =
        element * - atom:* {
            (attribute * { text }
             | text
             | anyElement)*
        }
    """
    category = etree.SubElement(xml, "category")
    atomCommonAttributes(category, attributes, skip=("term", "scheme", "label"))
    category.attrib["term"] = attributes["term"]

    if "scheme" in attributes:
        category.attrib["scheme"] = atomUri(attributes["scheme"])

    if "label" in attributes:
        category.attrib["label"] = attributes["label"]

    category.text = text  # NOTE: text only


def atomContributor(xml, elements, attributes=None):
    """
    atomContributor = element atom:contributor { atomPersonConstruct }
    """
    contributor = etree.SubElement(xml, "contributor")
    atomPersonConstruct(contributor, elements, attributes)


def atomGenerator(xml, text, attributes=None):
    """
    atomGenerator = element atom:generator {
        atomCommonAttributes,
        attribute uri { atomUri }?,
        attribute version { text }?,
        text
    }
    """
    generator = etree.SubElement(xml, "generator")
    atomCommonAttributes(generator, attributes, skip=("uri", "version"))

    if attributes:
        if "uri" in attributes:
            generator.attrib["uri"] = atomUri(attributes["uri"])

        if "version" in attributes:
            generator.attrib["version"] = attributes["version"]

    generator.text = text


def atomIcon(xml, uri, attributes=None):
    """
    atomIcon = element atom:icon {
        atomCommonAttributes,
        (atomUri)
    }
    """
    icon = etree.SubElement(xml, "icon")
    atomCommonAttributes(icon, attributes)
    icon.text = atomUri(uri)


def atomId(xml, uri, attributes=None):
    """
    atomId = element atom:id {
        atomCommonAttributes,
        (atomUri)
    }
    """
    id_ = etree.SubElement(xml, "id")
    atomCommonAttributes(id_, attributes)
    id_.text = atomUri(uri)


def atomLink(xml, text, attributes):
    """
    atomLink =
        element atom:link {
            atomCommonAttributes,
            attribute href { atomUri },
            attribute rel { atomNCName | atomUri }?,
            attribute type { atomMediaType }?,
            attribute hreflang { atomLanguageTag }?,
            attribute title { text }?,
            attribute length { text }?,
            undefinedContent
        }

    atomNCName = xsd:string { minLength = "1" pattern = "[^:]*" }
    """
    link = etree.SubElement(xml, "link")
    atomCommonAttributes(link, attributes, skip=("href", "rel", "type", "hreflang",
                                                 "title", "length"))
    link.attrib["href"] = atomUri(attributes["href"])

    if "rel" in attributes:
        link.attrib["rel"] = atomUri(attributes["rel"])  # NOTE: atomUri only

    if "type" in attributes:
        link.attrib["type"] = atomMediaType(attributes["type"])

    if "hreflang" in attributes:
        link.attrib["hreflang"] = atomLanguageTag(attributes["hreflang"])

    if "title" in attributes:
        link.attrib["title"] = attributes["title"]

    if "length" in attributes:
        link.attrib["length"] = attributes["length"]

    if text is not None and len(text) > 0:
        link.text = text  # NOTE: text only


def atomLogo(xml, uri, attributes=None):
    """
    atomLogo = element atom:logo {
        atomCommonAttributes,
        (atomUri)
    }
    """
    logo = etree.SubElement(xml, "logo")
    atomCommonAttributes(logo, attributes)
    logo.text = atomUri(uri)


def atomPublished(xml, dateTime, attributes=None):
    """
    atomPublished = element atom:published { atomDateConstruct }
    """
    published = etree.SubElement(xml, "published")
    atomDateConstruct(published, dateTime, attributes)


def atomRights(xml, obj, attributes):
    """
    atomRights = element atom:rights { atomTextConstruct }
    """
    rights = etree.SubElement(xml, "rights")
    atomTextConstruct(rights, obj, attributes)


def atomSubtitle(xml, obj, attributes):
    """
    atomSubtitle = element atom:subtitle { atomTextConstruct }
    """
    subtitle = etree.SubElement(xml, "subtitle")
    atomTextConstruct(subtitle, obj, attributes)


def atomSummary(xml, obj, attributes):
    """
    atomSummary = element atom:summary { atomTextConstruct }
    """
    summary = etree.SubElement(xml, "summary")
    atomTextConstruct(summary, obj, attributes)


def atomTitle(xml, obj, attributes):
    """
    atomTitle = element atom:title { atomTextConstruct }
    """
    title = etree.SubElement(xml, "title")
    atomTextConstruct(title, obj, attributes)


def atomUpdated(xml, dateTime, attributes=None):
    """
    atomUpdated = element atom:updated { atomDateConstruct }
    """
    updated = etree.SubElement(xml, "updated")
    atomDateConstruct(updated, dateTime, attributes)


def get_person_elements(source):
    elements = {}

    for name, value in iteritems(source):
        if name == "href":
            elements["uri"] = value

        elif value is not None and len(value) > 0:
            elements[name] = value

    return elements


types = {
    "text/plain": "text",
    "text/html": "html",
    "application/xhtml+xml": "xhtml"
}


def get_text_attributes(source):
    attributes = {}

    for name, value in iteritems(source):
        if name == "type":
            attributes["type"] = types.get(value, value)

        elif name == "language":
            attributes["lang"] = value

        elif name == "value":
            pass

        elif value:
            attributes[name] = value

    return attributes


def atomSource(xml, source):  # pylint: disable=W0613
    """
    atomSource =
        element atom:source {
            atomCommonAttributes,
            (atomAuthor*
             & atomCategory*
             & atomContributor*
             & atomGenerator?
             & atomIcon?
             & atomId?
             & atomLink*
             & atomLogo?
             & atomRights?
             & atomSubtitle?
             & atomTitle?
             & atomUpdated?
             & extensionElement*)
        }
    """
    raise NotImplementedError("atomSource not supported")


def atomEntry(xml, entry):
    """
    atomEntry =
        element atom:entry {
            atomCommonAttributes,
            (atomAuthor*
             & atomCategory*
             & atomContent?
             & atomContributor*
             & atomId
             & atomLink*
             & atomPublished?
             & atomRights?
             & atomSource?
             & atomSummary?
             & atomTitle
             & atomUpdated
             & extensionElement*)
        }
    """
    xmlentry = etree.SubElement(xml, "entry")
    atomCommonAttributes(xmlentry)

    if "author" in entry:
        atomAuthor(xmlentry, elements=get_person_elements(entry["author"]), attributes=None)

    if "tags" in entry:
        for category in entry["tags"]:
            atomCategory(xmlentry, text=None, attributes=category)

    if "content" in entry:
        for content in entry["content"]:
            atomContent(xmlentry, obj=content["value"],
                        attributes=get_text_attributes(content))

    if "contributors" in entry:
        for contributor in entry["contributors"]:
            atomContributor(xmlentry, elements=get_person_elements(contributor), attributes=None)

    atomId(xmlentry, uri=entry["id"])

    if "links" in entry:
        for link in entry["links"]:
            atomLink(xmlentry, text=None, attributes=link)

    if "published" in entry:
        atomPublished(xmlentry, dateTime=entry["published"])

    if "rights" in entry:
        atomRights(xmlentry, obj=entry["rights"]["value"],
                   attributes=get_text_attributes(entry["rights"]))

    if "source" in entry:
        atomSource(xmlentry, entry["source"])

    if "summary" in entry:
        atomSummary(xmlentry, obj=entry["summary"]["value"],
                    attributes=get_text_attributes(entry["summary"]))

    atomTitle(xmlentry, obj=entry["title"]["value"],
              attributes=get_text_attributes(entry["title"]))

    atomUpdated(xmlentry, dateTime=entry["updated"])

    # NOTE: extensionElement not supported


def atomFeed(feed, entries):
    """
    atomFeed =
        element atom:feed {
            atomCommonAttributes,
            (atomAuthor*
             & atomCategory*
             & atomContributor*
             & atomGenerator?
             & atomIcon?
             & atomId
             & atomLink*
             & atomLogo?
             & atomRights?
             & atomSubtitle?
             & atomTitle
             & atomUpdated
             & extensionElement*),
            atomEntry*
        }
    """
    atom = etree.Element("feed", xmlns="http://www.w3.org/2005/Atom")
    atomCommonAttributes(atom)

    if "author" in feed:
        atomAuthor(atom, elements=get_person_elements(feed["author"]))

    if "tags" in feed:
        for category in feed["tags"]:
            atomCategory(atom, text=None, attributes=category)

    if "contributors" in feed:
        for contributor in feed["contributors"]:
            atomContributor(atom, elements=get_person_elements(contributor))

    if "generator" in feed:
        attributes = copy.copy(feed["generator"])

        if "name" in attributes:
            del attributes["name"]

        if "href" in attributes:
            attributes["uri"] = attributes["href"]
            del attributes["href"]

        atomGenerator(atom, text=feed["generator"]["name"], attributes=attributes)

    if "icon" in feed:
        atomIcon(atom, uri=feed["icon"])

    atomId(atom, uri=feed["id"])

    if "links" in feed:
        for link in feed["links"]:
            atomLink(atom, text=None, attributes=link)

    if "logo" in feed:
        atomLogo(atom, uri=feed["logo"])

    if "rights" in feed:
        atomRights(atom, obj=feed["rights"]["value"],
                   attributes=get_text_attributes(feed["rights"]))

    if "subtitle" in feed:
        atomSubtitle(atom, obj=feed["subtitle"]["value"],
                     attributes=get_text_attributes(feed["subtitle"]))

    atomTitle(atom, obj=feed["title"]["value"],
              attributes=get_text_attributes(feed["title"]))

    atomUpdated(atom, dateTime=feed["updated"])

    # NOTE: extensionElement not supported

    for entry in entries:
        atomEntry(atom, entry)

    return atom


def get_xml(head, entries):
    atom = atomFeed(head, entries)

    return etree.tostring(atom, xml_declaration=True, encoding="utf-8")
