"""Process app icon"""
import subprocess
import shutil

from pathlib import Path
from typing import List, Optional, Union

from .discover import walk_path


class SipsConversionException(Exception):
    def __init__(self, p):
        self.message = p.stdout.decode("utf-8").strip()
        super().__init__(self.message)


def is_icon_file(f: Path, sap_code: str, name_pattern: str) -> bool:
    """Determine if icon file is the right file
    :param f (Path): icon file path
    :param sap_code (str): Adobe SAP code for product being processed
    :paaram name_pattern (str): icon filename pattern to test"""
    return sap_code in str(f) and name_pattern in str(f)


def find_app_icon(installer_pkg: Path, sap_code: str, name_pattern: str = 'appIcon2x') -> Optional[Union[Path, List, None]]:
    """Find corresponding app icon
    :param installer_pkg (Path): installer pkg to process icons from
    :param sap_code (str): Adobe SAP code for product being processed
    :paaram name_pattern (str): icon filename pattern to test"""
    icon = [f for f in walk_path(installer_pkg, file_ext=None) if is_icon_file(f, sap_code, name_pattern)]
    icon = icon[0] if len(icon) == 1 or len(icon) > 1 else icon
    result = icon or None

    return result


def convert_icns_to_png(icon_src: Path, icon_dst: Path, dry_run: bool = False) -> None:
    """Use inbuilt sips to convert icns file to png
    :param icon_src (Path): source icon to copy
    :param icon_dst (Path): destination of source icon"""
    cmd = ["/usr/bin/sips", "-z", "256", "-s", "format", "png", icon_src, "--out", icon_dst]

    if not dry_run:
        p = subprocess.run(cmd, capture_output=True)

        if p.returncode == 0 and "Warning" in p.stdout.decode("utf-8"):
            raise SipsConversionException(p)


def copy_icon(icon_src: Path, icon_dst: Path, dry_run: bool = False) -> bool:
    """Copy app icon into repo
    :param icon_src (Path): source icon to copy
    :param icon_dst (Path): destination of source icon"""
    result = False

    if not dry_run and not icon_dst.exists():
        if icon_dst.suffix == '.icns':
            convert_icns_to_png(icon_src, icon_dst, dry_run)
        else:
            shutil.copy(icon_src, icon_dst)

        result = icon_dst.exists()

        if result:
            print(f"Copied icon {str(icon_dst.name)!r} to icons folder")
    elif dry_run:
        if not icon_dst.exists():
            print(f"Copy icon {str(icon_dst.name)!r} to icons folder")
        else:
            print(f"Icon {str(icon_dst.name)!r} exists in icons folder")

    return result
