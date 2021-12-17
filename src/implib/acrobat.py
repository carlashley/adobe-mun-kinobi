from pathlib import Path

from .xmltodict import convert_xml, read_xml


# Used only for pulling the version to use.
ACROBAT_APP_VER_ATTR = "com.adobe.acrobat.DC.viewer.app.pkg.MUI"

# Additional receipt data that needs to be updated in the pkginfo file for Adobe Acrobat DC.
ACROBAT_RECEIPT_ATTRS = ["com.adobe.acrobat.DC.viewer.app.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.appsupport.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.browser.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.print_automator.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.print_pdf_services.pkg.MUI"]


def flatten_choices(choices: list) -> list:
    """Flatten package choices data out from a Distribution file"""
    result = list()

    # Get a little messy
    for choice in choices:
        if isinstance(choice, list):
            for subchoice in choice:
                result.append(subchoice)
        elif isinstance(choice, dict):
            result.append(choice)

    return result


def optional_receipts(dist_file: Path) -> list:
    """Process the Distribution file from the Adobe Acrobat installer package
    :param dist_file (Path): the Distribution script from the Acrobat installer"""
    result = list()
    dist_xml = convert_xml(read_xml(dist_file))
    receipts = flatten_choices([c["pkg-ref"] for c in dist_xml["installer-gui-script"]["choice"]])

    for receipt in receipts:
        receipt_id = receipt["id"]
        if receipt_id in ACROBAT_RECEIPT_ATTRS:
            result.append({"packageid": receipt["id"], "version": receipt["version"]})

    return result


def app_version(pkg_info: Path) -> str:
    """Determine the correct Acrobat version from the application package
    :param pkg_info  (Path): path to the PackageInfo file to parse"""
    pkginfo_xml = convert_xml(read_xml(pkg_info))
    result = pkginfo_xml["pkg-info"]["version"]

    return result
