"""Adobe Package"""
import plistlib

from dataclasses import dataclass, field
from pathlib import Path
from sys import exit
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from urllib.parse import urlparse

from .appicon import find_app_icon
from .xmltodict import convert_xml, read_xml
from . import acrobat
from . import application


if TYPE_CHECKING:
    from .munkirepo import MunkiImportPreferences

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

# Supported locales
SUPPORTED_LOCALES = ["ar_AE",
                     "cs_CZ",
                     "da_DK",
                     "de_DE",
                     "en_AE",
                     "en_GB",
                     "en_IL",
                     "en_US",
                     "en_XM",
                     "es_ES",
                     "es_MX",
                     "fi_FI",
                     "fr_CA",
                     "fr_FR",
                     "fr_MA",
                     "fr_XM",
                     "he_IL",
                     "hu_HU",
                     "it_IT",
                     "ja_JP",
                     "ko_KR",
                     "nb_NO",
                     "nl_NL",
                     "no_NO",
                     "pl_PL",
                     "pt_BR",
                     "ru_RU",
                     "sv_SE",
                     "th_TH",
                     "tr_TR",
                     "uk_UA",
                     "zh_CN",
                     "zh_TW"]


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
    app_icon: Union[Path, None] = field(compare=False)
    icon_dir: Path = field(compare=False, repr=False)
    description: str = field(compare=False)
    imported: bool = field(default=False, compare=False)

    def __post_init__(self):
        self.pkginfo_file = f"{self.pkg_name}-{self.version}"
        self.icon = self.icon_dir.joinpath(f"{self.pkg_name}-{self.version}.png")


def list_sap_codes() -> None:
    """List SAP codes with human friendly names"""
    padding = len(max([sc for sc, _ in SAP_CODES.items()], key=len))
    source = ("https://helpx.adobe.com/uk/enterprise/admin-guide.html/uk/enterprise/"
              "kb/apps-deployed-without-base-versions.ug.html")

    print(f"Sourced from: {source}")

    for sap_code, prod_name in SAP_CODES.items():
        print(f" {sap_code.ljust(padding)} - {prod_name}")

    exit()


def list_locales() -> None:
    """List supported locale codes"""
    print("Supported locales:")

    for locale in SUPPORTED_LOCALES:
        print(f" - {locale!r}")

    exit()


def get_min_os_ver(f: Path) -> str:
    """Get the minium OS version required
    :param f (Path): Info.plist file to pull OS requirements from"""
    result = None

    with open(f, "rb") as plist_file:
        plist = plistlib.load(plist_file)
        result = plist.get("LSMinimumSystemVersion")

    return result


def process_hdmedia(hdmedia: Union[List, Dict[Any, Any]]) -> Dict[Any, Any]:
    """Pull out the relevant HDMedia dictionary based on SAP code values
    :param hdmedia (list): list of HDMedia dictionaries"""
    # Note: HDMedia can be either a list or a dict, depending on whether
    #       the value is being passed in from Adobe Acrobat or a
    #       optionXML.xml file from other Adobe apps
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
    # Note: The Acrobat optionXML.xml file does not appear to have the
    #       same HDMedias key structure as other packages, so handle
    #       this through the try/except catcher
    try:
        hdmedia = process_hdmedia(install_info["Medias"]["Media"])
    except TypeError:
        hdmedia = process_hdmedia(install_info["HDMedias"]["HDMedia"])

    result = dict()
    sap_code = hdmedia["SAPCode"]
    arch = install_info["ProcessorArchitecture"]
    display_name = process_display_name(sap_code)

    result["pkg_name"] = install_info.get("PackageName")
    result["display_name"] = display_name
    result["arch"] = "x86_64" if arch and arch == "x64" else arch
    result["version"] = hdmedia.get("productVersion")
    result["sap_code"] = sap_code

    return result


def process_app_description(install_pkg: Path, sap_code: str, locale: str) -> str:
    """Process the Application.json file to get a description to use in munki
    :param install_pkg (Path): install package to process app description from
    :param sap_code (str): application SAP code
    :param locale (str): locale value used when building the package"""
    json_file = application.find_application_json(install_pkg, sap_code)
    app_json = application.read_json_file(json_file)

    try:
        desc_locales = app_json["ProductDescription"]["DetailedDescription"]["Language"]
    except KeyError:
        desc_locales = app_json["ProductDescription"]["Tagline"]["Language"]

    descriptions = list()

    # Adobe does weird stuff, like duplicate strings...
    for desc in desc_locales:
        _locale = desc["locale"]
        if _locale == locale and _locale in SUPPORTED_LOCALES and desc["value"] not in descriptions:
            descriptions.append(desc["value"])

    result = " ".join(descriptions) if len(descriptions) > 1 else "".join(descriptions)

    return result


def process_package(install_pkg: Path, uninstall_pkg: Path, munkiimport_prefs: 'MunkiImportPreferences',
                    locale: str = "en_GB", dmg_file: Optional[Path] = None) -> AdobePackage:
    """Process an installer package for product information
    :param install_pkg (Path): path to install package
    :param uninstall_pkg (Path): path to uninstall package
    :param munkiimport_prefs (MunkiImportPreferences): instance of MunkiImportPreferences
    :param locale (str): locale used when building package
    :param dmg_file (str): DMG file to mount (currently only applies to Acrobat)"""
    opt_xml = install_pkg.joinpath("Contents/Resources/optionXML.xml")
    info_plist = install_pkg.joinpath("Contents/Info.plist")
    install_info = convert_xml(read_xml(opt_xml))["InstallInfo"]

    package = process_opt_xml(install_info)
    package["installer"] = install_pkg
    package["uninstaller"] = uninstall_pkg
    package["min_os"] = get_min_os_ver(info_plist)
    package["blocking_apps"] = BLOCKING_APPS.get(package["sap_code"], list())
    package["receipts"] = list()
    package["app_icon"] = find_app_icon(install_pkg, package["sap_code"])
    package["icon_dir"] = Path(urlparse(str(munkiimport_prefs.icon_directory)).path)

    if package["sap_code"] != "APRO":
        package["description"] = process_app_description(install_pkg, package["sap_code"], locale)

    if package["sap_code"] == "APRO":
        acrobat_patches = acrobat.package_patch(dmg_file)  # type: ignore[arg-type]
        package["description"] = "Adobe Acrobat Pro DC makes your job easier every day with the trusted PDF converter."
        package.update(acrobat_patches)

    result = AdobePackage(**package)

    return result
