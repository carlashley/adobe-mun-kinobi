"""XML to Native dict conversion"""
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict
from xml.etree import ElementTree

# Used only for pulling the version to use.
ACROBAT_APP_VER_ATTR = "com.adobe.acrobat.DC.viewer.app.pkg.MUI"

# Additional receipt data that needs to be updated in the pkginfo file for Adobe Acrobat DC.
ACROBAT_RECEIPT_ATTRS = ["com.adobe.acrobat.DC.viewer.app.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.appsupport.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.browser.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.print_automator.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.print_pdf_services.pkg.MUI"]


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
