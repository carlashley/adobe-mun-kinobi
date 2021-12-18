"""Handling the Acrobat package"""
import shutil

from pathlib import Path
from pprint import pformat
from typing import Any, Dict, Generator, List, Union

from .pkgutil import expand_package
from .xmltodict import convert_xml, read_xml
from . import dmg


# Used only for pulling the version to use.
ACROBAT_APP_VER_ATTR = "com.adobe.acrobat.DC.viewer.app.pkg.MUI"

# Additional receipt data that needs to be updated in the pkginfo file for Adobe Acrobat DC.
ACROBAT_RECEIPT_ATTRS = ["com.adobe.acrobat.DC.viewer.app.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.appsupport.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.browser.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.print_automator.pkg.MUI",
                         "com.adobe.acrobat.DC.viewer.print_pdf_services.pkg.MUI"]


def find_installer(mount_path: Path, pattern: str = "*/*.pkg", installer_prefix: str = "Installer") -> Path:
    """Find the Adobe Acrobat installer from the mounted Acrobat DMG
    :param mount_path (str): mounted path of DMG to glob packages for
    :param pattern (str): glob pattern
    :param installer_prefix (str): installer prefix to test if the globbed item is the installer package"""
    return [f for f in mount_path.glob(pattern) if installer_prefix in str(f)][0]


def flatten_choices(choices: List[Union[Dict, List]]) -> List[Dict]:
    """Flatten package choices data out from a Distribution file as the choices can be nested values
    :param choices (list or dict): choices to flatten out"""
    result = list()

    # Get a little messy
    for choice in choices:
        if isinstance(choice, list):
            for subchoice in choice:
                result.append(subchoice)
        elif isinstance(choice, dict):
            result.append(choice)

    return result


def optional_receipts(dist_file: Path) -> Generator:
    """Process the Distribution file from the Adobe Acrobat installer package for optional receipts
    :param dist_file (Path): the Distribution script from the Acrobat installer"""
    dist_xml = convert_xml(read_xml(dist_file))
    receipts = flatten_choices([c["pkg-ref"] for c in dist_xml["installer-gui-script"]["choice"]])

    for receipt in receipts:
        receipt_id = receipt["id"]
        if receipt_id in ACROBAT_RECEIPT_ATTRS:
            receipt_dict = {"packageid": receipt["id"],
                            "version": receipt["version"]}
            yield receipt_dict


def minimum_os_ver(dist_file: Path) -> Union[str, None]:
    """Process the Distribution file from the Adobe Acrobat installer package for minimum OS version
    :param dist_file (Path): the Distribution script from the Acrobat installer"""
    dist_xml = convert_xml(read_xml(dist_file))

    try:
        allowed_os_vers = dist_xml["installer-gui-script"]['volume-check']['allowed-os-versions']
        result = allowed_os_vers['os-version']['min']
    except KeyError:
        result = None

    return result


def app_version(pkg_info: Path) -> str:
    """Determine the correct Acrobat version from the application package
    :param pkg_info  (Path): path to the PackageInfo file to parse"""
    pkginfo_xml = convert_xml(read_xml(pkg_info))
    result = pkginfo_xml["pkg-info"]["version"]

    return result


def package_info(pkg_path: Path, pkg_info_file: str = "application.pkg/PackageInfo") -> Path:
    """Return the full path to the PackageInfo file used for Adobe Acrobat version info
    :param pkg_path (Path): path to the expanded Acrobat package
    :param pkg_info_file (str): sub path of the PackageInfo file within the Acrobat package"""
    return pkg_path.joinpath(pkg_info_file)


def distribution_script(pkg_path: Path, dist_file: str = "Distribution") -> Path:
    """Return the full path to the Distribution script used by Adobe Acrobat
    :param pkg_path (Path): path to the expanded Acrobat package
    :param dist_file (str): sub path of the distribution script within the Acrobat package"""
    return pkg_path.joinpath(dist_file)


def cleanup(mount_path: Path, tmp_dir: Path) -> None:
    """Unmount and remove temporary expanded package
    :param mount_path (path): mount path to detach
    :param tmp_dir (path): path to the temporary working directory containing the expanded package"""
    if mount_path.exists():
        dmg.detach(mount_path)

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)


def package_patch(dmg_file: Path) -> Dict[Any, Any]:
    """Pull version and optional receipts data from the Adobe Acrobat package located in the Acrobat DMG
    :param dmg_file (Path): Acrobat DMG file to mount and process"""
    mount_path = dmg.mount(dmg_file)
    installer = find_installer(mount_path)
    tmp_pkg = expand_package(installer)
    pkg_info_file = package_info(tmp_pkg)
    dist_xml_file = distribution_script(tmp_pkg)
    version = app_version(pkg_info_file)
    receipts = [rd for rd in optional_receipts(dist_xml_file)]
    min_os_ver = minimum_os_ver(dist_xml_file)

    result = dict()
    result["version"] = version
    result["receipts"] = receipts  # type: ignore[assignment]

    # Only include the correct min_os_ver if it's in the Distribution script of the Acrobat package
    if min_os_ver:
        result["min_os"] = min_os_ver

    cleanup(mount_path, tmp_pkg)

    return result
