import plistlib

from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

from .discover import walk_path, pkginfo_file_ext


def read_pkginfo(pkginfo: Union[str, Path]) -> Dict[Any, Any]:
    """Read the specified pkginfo file
    :param pkginfo (str, Path): path to the pkginfo file"""
    result: Dict[Any, Any] = dict()

    with open(pkginfo, "rb") as f:
        result = plistlib.load(f)

    return result


def write_pkginfo(pkginfo: Union[str, Path], data: Dict[Any, Any]) -> None:
    """Write new data to the specified pkginfo file
    :param pkginfo (str, Path): path to the pkginfo file
    :param data (dict): data to write to the pkginfo file"""
    with open(pkginfo, "wb") as f:
        plistlib.dump(data, f)


def update(pkginfo: Union[str, Path], dry_run: bool = False, receipts: Optional[Dict] = None) -> None:
    """Update the specified pkginfo with additional data
    :param pkginfo (str, Path, Purepath): path to the pkginfo file to update
    :param blocking_apps (list, set): any blocking apps to update
    :param receipts (dict): any receipts that need to be updated in the pkginfo"""
    if not dry_run:
        patch = dict()
        pkginfo_data = read_pkginfo(pkginfo)

        if receipts:
            patch["receipts"] = receipts

        if patch:
            pkginfo_data.update(patch)
            write_pkginfo(pkginfo, pkginfo_data)
            print(f"Updated pkginfo {str(pkginfo)!r}")


def existing_pkginfo(munki_repo: Path, file_ext: str = pkginfo_file_ext()) -> list:
    """Returns existing pkginfo files from the munki repo
    :param munki_repo (Path): munki repo"""
    munki_repo = Path(urlparse(str(munki_repo)).path).joinpath("pkgsinfo")
    result = walk_path(munki_repo, file_ext)

    return result
