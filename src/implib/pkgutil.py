"""pkgutil wrapper"""
import subprocess

from pathlib import Path
from tempfile import gettempdir


class PkgutilException(Exception):
    """pkgutil Exception
    :param p (subprocess.CompletedProcess): subprocess"""
    def __init__(self, p: subprocess.CompletedProcess) -> None:
        self.exit_code = p.returncode
        self.stdout = p.stdout.strip()
        self.stderr = p.stderr.strip()
        self.message = f"pkgutil exited with exit code {self.exit_code}: {self.stdout or self.stderr}"
        super().__init__(self.message)


def expand_package(pkg: Path, tmp_dir: Path = Path(gettempdir()).joinpath("acrobat")) -> Path:
    """Expand a package into a temporary directory
    :param pkg (str): package to expand
    :param tmp_dir (str): temporary directory to expand to"""
    result = Path(tmp_dir)
    cmd = ["/usr/sbin/pkgutil", "--expand", pkg, tmp_dir]
    p = subprocess.run(cmd, capture_output=True, encoding="utf-8")

    if not p.returncode == 0:
        raise PkgutilException(p)

    return result
