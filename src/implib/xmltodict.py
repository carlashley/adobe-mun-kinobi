"""XML to Native dict conversion"""
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict
from xml.etree import ElementTree


def read_xml(f: Path) -> ElementTree.Element:
    """Read an XML file and return the root"""
    with open(f, "r") as xml_file:
        return ElementTree.XML(xml_file.read())


def convert_xml(root: ElementTree.Element) -> Dict[Any, Any]:
    """Convert XML to native Dict based on https://stackoverflow.com/a/32842402
    :param root (ElementTree.Element): XML object to convert"""
    result: Dict[Any, Any] = dict()
    result.update({root.tag: {} if root.attrib else None})
    children = list(root)

    if children:
        dd = defaultdict(list)

        for dc in map(convert_xml, children):
            for k, v in dc.items():
                dd[k].append(v)

        result = {root.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}

    if root.attrib:
        result[root.tag].update((k, v) for k, v in root.attrib.items())

    if root.text:
        text = root.text.strip()

        if children or root.attrib:
            if text:
                result[root.tag]["text"] = text
        else:
            result[root.tag] = text

    return result
