"""hdiutil wrapper"""
import plistlib
import subprocess

from pathlib import Path


class DMGException(Exception):
    """DMG Exception
    :param p (subprocess.CompletedProcess): subprocess"""
    def __init__(self, p: subprocess.CompletedProcess) -> None:
        self.exit_code = p.returncode
        self.stdout = p.stdout.decode("utf-8")
        self.stderr = p.stderr.decode("utf-8")
        self.message = f"hdiutil exited with exit code {self.exit_code}: {self.stdout or self.stderr}"
        super().__init__(self.message)


def get_mount_point(s: bytes) -> Path:
    """Resolve the mount point of a DMG file
    :param s (bytes): property list byte string"""
    entities = plistlib.loads(s)["system-entities"]
    mount_point = "".join([entity["mount-point"] for entity in entities if entity.get("mount-point")])

    return Path(mount_point)


def mount(dmg: Path) -> Path:
    """Mount a DMG and return the mount point
    :param dmg (str): path to DMG file to mount"""
    cmd = ["/usr/bin/hdiutil", "attach", "-plist", "-nobrowse", dmg]
    p = subprocess.run(cmd, capture_output=True)  # type: ignore[arg-type]

    if p.returncode == 0:
        return get_mount_point(p.stdout)
    else:
        raise DMGException(p)


def detach(vol: Path) -> None:
    """Detach a mounted DMG
    :param vol (str): volume file path the DMG is mounted to"""
    cmd = ["/usr/bin/hdiutil", "detach", "-quiet", vol]
    p = subprocess.run(cmd, capture_output=True)  # type: ignore[arg-type]

    if p.returncode != 0:
        raise DMGException(p)
