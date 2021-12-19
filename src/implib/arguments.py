"""Construct arguments"""
import argparse
import sys

from pathlib import Path
from urllib.parse import urlparse

from .package import SAP_CODES, SUPPORTED_LOCALES, list_sap_codes, list_locales


__NAME__ = "adobe-mun-kinobi"
__VERSION__ = "1.0.20211219"
__LICENSE__ = "Apache License 2.0"
__VERSION_STRING__ = f"{__NAME__} v{__VERSION__} licensed for use under the {__LICENSE__} license"


def parse_repo_url(repo_url: Path) -> str:
    """Convert repo_url to string and fix the file scheme that Path botches
    :param repo_url (Path): repo url to fix when botched by Path"""
    url = urlparse(str(repo_url))
    result = f"{url.scheme}://{url.path}" if url.scheme == "file" else str(repo_url)

    return result


def construct() -> argparse.Namespace:
    default_munki_repo = "file:///Volumes/munki_repo"
    default_pkg_dir = "apps"
    default_category = "Creativity"
    default_catalog = "testing"
    default_developer = "Adobe"
    default_min_munki_ver = "2.1"
    default_display_name_suffix = "Creative Cloud"
    default_locale = "en_GB"
    sap_codes = sorted([code for code in SAP_CODES])
    list_sap_codes_arg = "--list-sap-codes"
    parser = argparse.ArgumentParser()

    parser.add_argument("--adobe-dir",
                        type=str,
                        dest="adobe_dir",
                        metavar="[dir]",
                        help="directory containing unzipped Adobe installers")

    parser.add_argument("--locale",
                        type=str,
                        dest="locale",
                        metavar="[locale]",
                        default=default_locale,
                        choices=SUPPORTED_LOCALES,
                        help=f"override the default locale {default_locale!r} for all packages processed")

    parser.add_argument("--category",
                        type=str,
                        dest="category",
                        required=False,
                        metavar="[category]",
                        default=default_category,
                        help=f"override the default category {default_category!r} for all packages processed")

    parser.add_argument("--catalog",
                        type=str,
                        dest="catalog",
                        required=False,
                        metavar="[catalog]",
                        default=default_catalog,
                        help=f"override the default catalog {default_catalog!r} for all packages processed")

    parser.add_argument("--developer",
                        type=str,
                        dest="developer",
                        required=False,
                        metavar="[developer]",
                        default=default_developer,
                        help=f"override the default developer {default_developer!r} for all packages processed")

    parser.add_argument("--munki-repo",
                        type=str,
                        dest="munki_repo",
                        required=False,
                        metavar="[dir]",
                        help=f"override or use a custom munki repo path, defaults to {default_munki_repo!r}")

    parser.add_argument("--munki-subdir",
                        type=str,
                        dest="munki_subdir",
                        required=False,
                        metavar="[dir]",
                        default=default_pkg_dir,
                        help=f"override the default package directory {default_pkg_dir!r} for all packages processed")

    parser.add_argument("--min-munki-version",
                        type=str,
                        dest="min_munki_ver",
                        required=False,
                        metavar="[min munki version]",
                        default=default_min_munki_ver,
                        help=f"override the default minimum version of munki {default_min_munki_ver!r} for all packages processed")

    parser.add_argument("--min-os-ver",
                        type=str,
                        dest="min_os_ver",
                        required=False,
                        metavar="[min os ver]",
                        help="override the minimum macOS version for all packages processed")

    parser.add_argument("--suffix",
                        type=str,
                        dest="suffix",
                        required=False,
                        metavar="[suffix]",
                        default=default_display_name_suffix,
                        help=f"override the default display name suffix {default_display_name_suffix!r} for all packages processed")

    parser.add_argument("--import-sap-code",
                        type=str,
                        nargs="+",
                        dest="import_sap_code",
                        required=False,
                        metavar="[code]",
                        default=sap_codes,
                        choices=sap_codes,
                        help=f"import specific Adobe products by SAP code, use {list_sap_codes_arg!r} to view codes")

    parser.add_argument("--list-locales",
                        action="store_true",
                        dest="list_locales",
                        help="list supported locale codes")

    parser.add_argument("--list-sap-codes",
                        action="store_true",
                        dest="list_sap_codes",
                        help="list Adobe products SAP codes")

    parser.add_argument("-n", "--dry-run",
                        action="store_true",
                        dest="dry_run",
                        required=False,
                        help="performs a dry run (outputs import commands to stdout)")

    parser.add_argument("-v", "--version",
                        action="version",
                        version=__VERSION_STRING__)

    result = parser.parse_args()

    if result.list_sap_codes:
        list_sap_codes()

    if result.list_locales:
        list_locales()

    if not result.list_sap_codes and not result.list_locales and not result.adobe_dir:
        name = str(Path(sys.argv[0]).name)
        parser.print_usage(sys.stderr)
        print(f"{name}: error: the following arguments are required: --adobe-dir")
        sys.exit(1)

    return result
