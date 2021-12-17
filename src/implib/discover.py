"""Functions related to discovery of Adobe files/packages"""
import plistlib
import re

from os import walk
from pathlib import Path
from typing import Any, Dict


def is_installer(f: Path, file_ext: str = ".pkg", install_prefix: str = "_Install") -> bool:
    """Determines if the specified package is an installer
    :param f (Path): file path"""
    return install_prefix in str(f) and file_ext in str(f)


def resolve_product_name(f: Path, file_ext: str = ".pkg", install_prefix: str = "_Install",
                         uninstall_prefix: str = "_Uninstall") -> str:
    """Resolves the product name for the specified file path
    :param f (Path): file path
    :param file_ext (str): file extension
    :param install_prefix (str): the string indicating the install package as named by
                                 default as generated by Adobe
    :param uninstall_prefix (str): the string indicating the uninstall package as named
                                   by default as generated by Adobe"""
    reg_pattern = re.compile(rf"{install_prefix}|{uninstall_prefix}")
    result = str(Path(re.sub(reg_pattern, "", str(f))).name)

    return result


def walk_path(d: Path, file_ext: str = ".pkg") -> list:
    """Walk subdirectories in a specified path for the specified file extension
    :param d (Path): directory to traverse searching for specific file extensions
    :param file_ext (str): the file extension to filter on"""
    result = list()
    found_files = set()
    d = d.expanduser()

    if d.exists():
        for path_root, dirs, files in walk(d):
            basepath = Path(path_root)

            if file_ext in [".pkg", ".dmg"]:
                f = Path(path_root)

                if file_ext == ".dmg":
                    dmg_glob = [f for f in basepath.glob("*.dmg")]
                    dmg_file = "".join([str(f) for f in dmg_glob if re.search(r"APRO\d+", str(f))])
                    f = f.joinpath(dmg_file)

                # if file_ext == ".pkg":
                #     f = path_root
                # elif file_ext == ".dmg":
                #     if any([f.endswith(file_ext) for f in files]):
                #         dmg_glob = [f for f in path_root.glob("*.dmg")]
                #         dmg_file = "".join([str(f) for f in dmg_glob if re.search(r"APRO\d+", str(f))])
                #         f = Path(dmg_file)

                if f and f.suffix == file_ext and f.exists():
                    found_files.add(f)
            else:
                for f in [Path(f) for f in files]:
                    f = basepath.joinpath(f).expanduser()

                    if f.suffix == file_ext and f.exists():
                        found_files.add(f)

    result = sorted([f for f in found_files])

    return result


def adobe_packages(d: Path) -> Dict[Any, Any]:
    """Discover Adobe installers and uninstallers in a specified path
    :param d (Path): the directory containing Adobe packages to import"""
    result: Dict[Any, Any] = dict()
    packages = walk_path(d)

    for pkg in packages:
        product_name = resolve_product_name(f=Path(pkg))
        product_dict = dict()

        if is_installer(f=pkg):
            acrobat_setup_dir = pkg.joinpath("Contents/Resources/Setup")
            product_dict["installer"] = pkg
            try:
                product_dict["dmg_file"] = list(walk_path(acrobat_setup_dir, file_ext=".dmg"))[0]
            except IndexError:
                pass  # Yeah, do _nothing_, this is how I want this to be handled.
        else:
            product_dict["uninstaller"] = pkg

        try:
            result[product_name].update(product_dict)
        except KeyError:
            result[product_name] = dict()
            result[product_name].update(product_dict)

    return result


def munkiimport_plist(plist: str = "com.googlecode.munki.munkiimport.plist") -> Path:
    """Find the relevant munkiimport preference file, prefers user over system file
    :param plist (str): basename of the munkiimport preference plist"""
    system = Path("/Library/Preferences").joinpath(plist)
    user = Path("~/Library/Preferences").expanduser().joinpath(plist)
    result = user if user.exists() else system

    return result


def read_import_prefs() -> Dict[Any, Any]:
    result: Dict[Any, Any] = dict()
    prefs_file = munkiimport_plist()

    if prefs_file.exists():
        with open(prefs_file, "rb") as f:
            result = plistlib.load(f)

    return result


def munki_repo() -> str:
    """Determine the munki repo path for importing
    :param munkiimport_plist (Path): path for the munkiimport preference file to source the repo value from"""
    default = "file:///Volumes/munki_repo"
    import_prefs = read_import_prefs()
    result = import_prefs.get("repo_url", default)

    return result


def pkginfo_file_ext() -> str:
    """Find the relevant pkginfo file extension"""
    default = ".plist"
    import_prefs = read_import_prefs()
    result = import_prefs.get("pkginfo_extension", default)

    return result


def pkgsinfo_path() -> Path:
    """Resolve the pkgsinfo directory"""
    repo = munki_repo()
    result = Path(repo).joinpath("pkgsinfo")

    return result
