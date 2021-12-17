"""Adobe Package"""
import plistlib
import shutil

from dataclasses import dataclass, field
from pathlib import Path
from sys import exit
from typing import Any, Dict, Optional, Union

from .xmltodict import convert_xml, read_xml
from . import acrobat
from . import dmg
from . import pkgutil

# Blocking apps
BLOCKING_APPS = {"APRO": ["Microsoft Word", "Safari"]}

# Current SAP codes for Adobe products.
# https://helpx.adobe.com/uk/enterprise/admin-guide.html/uk/enterprise/kb/apps-deployed-without-base-versions.ug.html
SAP_CODES = {"AEFT": "Adobe After Effects",
             "AICY": "Adobe InCopy",
             "AME": "Adobe Media Encoder",
             "APRO": "Adobe Acrobat Pro",
             "AUDT": "Adobe Audition",
             "CHAR": "Adobe Character Animator",
             "DRWV": "Adobe Dreamweaver",
             "ESHR": "Adobe Dimension",
             "FLPR": "Adobe Animate and Mobile Device Packaging",
             "FRSC": "Adobe Fresco",
             "IDSN": "Adobe InDesign",
             "ILST": "Adobe Illustrator",
             "KBRG": "Adobe Bridge",
             "LRCC": "Adobe Lightroom",
             "LTRM": "Adobe Lightroom Classic",
             "PHSP": "Adobe Photoshop",
             "PPRO": "Adobe Premiere Pro",
             "PRLD": "Adobe Prelude",
             "RUSH": "Adobe Premiere Rush",
             "SBSTA": "Adobe Substance Alchemist",
             "SBSTD": "Adobe Substance Designer",
             "SBSTP": "Adobe Substance Painter",
             "SPRK": "Adobe XD"}


@dataclass(eq=True, order=True)
class AdobePackage:
    pkg_name: str = field(compare=True)  # Compare on pkg_name, arch, and sap_code only
    arch: str = field(compare=True)
    sap_code: str = field(compare=True)
    display_name: str = field(compare=False)
    version: str = field(compare=False)
    min_os: str = field(compare=False)
    installer: Path = field(compare=False)
    uninstaller: Path = field(compare=False)
    receipts: list = field(compare=False)
    blocking_apps: list = field(compare=False)
    imported: bool = field(default=False, compare=False)

    def __post_init__(self):
        self.pkginfo_file = f"{self.pkg_name}-{self.version}"
        self.icon = f"{self.pkg_name}.png"


def list_sap_codes() -> None:
    """List SAP codes with human friendly names"""
    padding = len(max([sc for sc, _ in SAP_CODES.items()], key=len))
    source = ("https://helpx.adobe.com/uk/enterprise/admin-guide.html/uk/enterprise/"
              "kb/apps-deployed-without-base-versions.ug.html")

    print(f"Sourced from: {source}")

    for sap_code, prod_name in SAP_CODES.items():
        print(f" {sap_code.ljust(padding)} - {prod_name}")

    exit()


def get_min_os_ver(f: Path) -> str:
    """Get the minium OS version required
    :param f (Path): Info.plist file to pull OS requirements from"""
    result = None

    with open(f, "rb") as plist_file:
        plist = plistlib.load(plist_file)
        result = plist.get("LSMinimumSystemVersion")

    return result


def process_hdmedia(hdmedia: Union[list, dict]) -> Dict[Any, Any]:
    """Pull out the relevant HDMedia dictionary based on SAP code values
    :param hdmedia (list): list of HDMedia dictionaries"""
    # Note: HDMedia can be either a list or a dict, depending on whether
    #       the value is being passed in from Adobe Acrobat or a
    #       optionXML.xml file from other Adobe apps
    # print(hdmedia)
    try:
        for media in hdmedia:
            sap_code = media.get("SAPCode")

            if sap_code and sap_code in SAP_CODES:
                result = media
                break
    except AttributeError:
        result = hdmedia

    return result


def process_display_name(sap_code: str) -> str:
    """Parse out a display name for the package based on information in the media dict
    :param sap_code (str): SAP Code for the product"""
    return SAP_CODES[sap_code]


def process_opt_xml(install_info: Dict[Any, Any]) -> Dict[Any, Any]:
    """Process specific components of the OptionXML dict
    :param xml (dict): dictionary to pull values from
    :param acrobat (bool): process different values from the XML"""
    # result: dict  = {"pkg_name": str,
    #                  "display_name": str,
    #                  "arch": str,
    #                  "version": str,
    #                  "receipts": list(),
    #                  "blocking_apps": list(),
    #                  "sap_code": str}
    # result: Dict[Any, Any] = dict()

    # Note: The Acrobat optionXML.xml file does not appear to have the
    #       same HDMedias key structure as other packages, so handle
    #       this through the try/except catcher
    try:
        hdmedia = process_hdmedia(install_info["Medias"]["Media"])
    except TypeError:
        hdmedia = process_hdmedia(install_info["HDMedias"]["HDMedia"])

    # if hdmedia:
    result = dict()
    sap_code = hdmedia["SAPCode"]
    arch = install_info["ProcessorArchitecture"]
    display_name = process_display_name(sap_code)

    result["pkg_name"] = install_info.get("PackageName")
    result["display_name"] = display_name
    result["arch"] = "x86_64" if arch and arch == "x64" else arch
    result["version"] = hdmedia.get("productVersion")
    result["sap_code"] = sap_code
    result['blocking_apps'] = list()
    result['receipts'] = list()

    return result


def process_acrobat(expanded_pkg: Path) -> Dict[Any, Any]:
    """Process the Distribution file in Acrobat
    :param expanded_pkg (str): location of the expanded Acrobat package"""
    result = {"version": str,
              "receipts": list()}

    distribution_file = expanded_pkg.joinpath("Distribution")
    package_info = expanded_pkg.joinpath("application.pkg/PackageInfo")

    result["version"] = acrobat.app_version(package_info)
    result["receipts"] = acrobat.optional_receipts(distribution_file)

    return result


def glob_acrobat_installer(mount_path: Path, pattern: str = "*/*.pkg", installer_prefix: str = "Installer") -> Path:
    """Glob the mounted Acrobat DMG path for the installer
    :param mount_path (str): mounted path of DMG to glob packages for
    :param pattern (str): glob pattern
    :param installer_prefix (str): installer prefix to test if the globbed item is the installer package"""
    return [f for f in mount_path.glob(pattern) if installer_prefix in str(f)][0]


def parse_acrobat_patches(install_info: Dict[Any, Any], dmg_file: Path) -> Dict[Any, Any]:
    """Parse the Acrobat DMG file for patches to apply for importing
    :param install_info (dict): install info dictionary from package
    :param dmg_file (str): dmg file containing actual Acrobat installer"""
    result = process_opt_xml(install_info)
    mount_path = dmg.mount(dmg_file)
    globbed_installer = glob_acrobat_installer(mount_path)
    expanded_pkg = pkgutil.expand_package(globbed_installer)
    patches = process_acrobat(expanded_pkg)
    result.update(patches)

    if mount_path:
        dmg.detach(mount_path)

        if expanded_pkg.exists():
            shutil.rmtree(expanded_pkg)

    return result


def process_package(install_pkg: Path, uninstall_pkg: Path, dmg_file: Optional[Path] = None) -> AdobePackage:
    """Process an installer package for product information
    :param install_pkg (str): path to package
    :param dmg_file (str): DMG file to mount (currently only applies to Acrobat)"""
    opt_xml = install_pkg.joinpath("Contents/Resources/optionXML.xml")
    info_plist = install_pkg.joinpath("Contents/Info.plist")
    install_info = convert_xml(read_xml(opt_xml))["InstallInfo"]

    package = process_opt_xml(install_info)
    package["installer"] = install_pkg
    package["uninstaller"] = uninstall_pkg

    if dmg_file:
        acrobat_patches = parse_acrobat_patches(install_info, dmg_file)
        package.update(acrobat_patches)

    package["min_os"] = get_min_os_ver(info_plist)
    package["blocking_apps"] = BLOCKING_APPS.get(package["sap_code"], list())
    result = AdobePackage(**package)

    return result
