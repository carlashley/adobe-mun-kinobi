"""munkiimport wrapper"""
import subprocess

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from .package import AdobePackage


class MunkiImportException(Exception):
    """Munki Import Exception
    :param p (subprocess.CompletedProcess): subprocess"""
    def __init__(self, p: subprocess.CompletedProcess) -> None:
        self.exit_code = p.returncode
        self.stdout = p.stdout.decode("utf-8")
        self.stderr = p.stderr.decode("utf-8")
        self.message = f"munkiimport exited with exit code {self.exit_code}: {self.stdout or self.stderr}"
        super().__init__(self.message)


class MunkiRequiredKwargsException(Exception):
    """Munki Import Keyword Arguments Exception
    :param reqd_kwargs (list): list of required arguments"""
    def __init__(self, reqd_kwargs) -> None:
        self.reqd_kwargs = reqd_kwargs
        self.message = f"Missing value/s for required arguments: {self.reqd_kwargs!r}"
        super().__init__(self.message)


class MunkiInvalidKwargsException(Exception):
    """Munki Import Invalid Keyword Arguments Exception
    :param invalid_kwargs (list): list of invalid arguments
    :param valid_kwargs (list): list of valid arguments"""
    def __init__(self, invalid_kwargs, valid_kwargs) -> None:
        self.invalid_kwargs = invalid_kwargs
        self.valid_kwargs = valid_kwargs
        self.message = f"Invalid arguments: {self.invalid_kwargs!r}\nvalid arguments: {self.valid_kwargs!r}"
        super().__init__(self.message)


class MakeCatalogsException(Exception):
    """Make Catalogs Exception
    :param p (subprocess.CompletedProcess): subprocess"""
    def __init__(self, p: subprocess.CompletedProcess) -> None:
        self.exit_code = p.returncode
        self.stdout = p.stdout.decode("utf-8")
        self.stderr = p.stderr.decode("utf-8")
        self.message = f"makecatalogs exited with exit code {self.exit_code}: {self.stdout or self.stderr}"
        super().__init__(self.message)


def has_all_required_args(args: dict) -> None:
    """Check all required arguments are supplied
    :param args (dict): arguments to validate"""
    reqd_kwargs = ["--repo_url",
                   "--uninstallerpkg",
                   "--subdirectory"]

    if not all([arg in args for arg in reqd_kwargs]):
        missing_args = [arg for arg in reqd_kwargs if arg not in args]

        raise MunkiRequiredKwargsException(missing_args)


def has_valid_kwargs(args: dict) -> None:
    """Check all keyword arguments provided are valid
    :param args (dict): arguments to validate"""
    valid_kwargs = ["--category",
                    "--catalog",
                    "--developer",
                    "--repo_url",
                    "--subdirectory",
                    "--minimum_os_version",
                    "--displayname",
                    "--description",
                    "--name",
                    "--icon",
                    "--minimum_munki_version",
                    "--arch",
                    "--uninstallerpkg",
                    "--pkgvers"]

    invalid_args = [arg for arg, _ in args.items() if arg not in valid_kwargs]

    if invalid_args:
        raise MunkiInvalidKwargsException(invalid_args, valid_kwargs)


def pkginfo_file(output: str, munki_repo: str) -> Optional[Path]:
    """Parse output and return the success message
    :param output (str): output from munkiimport to parse
    :param munki_repo (str): base path of the munki_repo folder, e.g. file:///Volumes/munki_repo"""
    success_prefix = "Saved pkginfo to "
    f = "".join([line.strip() for line in output.splitlines()
                 if line.startswith(success_prefix)]).replace(success_prefix, "")

    munki_repo = urlparse(munki_repo).path
    pkginfo = f.replace(success_prefix, "").rstrip(".")
    result = Path(munki_repo).joinpath(pkginfo)

    return result


def package(pkg: AdobePackage, dry_run: bool = True, **kwargs) -> Optional[Path]:
    """Import a package in to the munki repo
    :param pkg (str): package path
    :dry_run (bool): perform a dry run (does not import packages)
    :kwargs (dict): additional arguments to pass to the munkiimport command"""
    result = None
    has_all_required_args(kwargs)  # Check all valid arguments are present in kwargs
    has_valid_kwargs(kwargs)  # Check all optional arguments are valid
    installer = pkg.installer
    uninstaller = pkg.uninstaller

    cmd = ["/usr/local/munki/munkiimport", "--nointeractive"]
    munki_repo = kwargs["--repo_url"]

    for k, v in kwargs.items():
        if dry_run and k in ["--uninstallerpkg"]:
            cmd.extend([k, uninstaller.name])
        else:
            cmd.extend([k, v])

    # Add any blocking apps
    if pkg.blocking_apps:
        for app in pkg.blocking_apps:
            cmd.extend(["--blocking-application", app])

    # Add the package to import as the last item
    if not dry_run:
        cmd.append(str(installer))
    else:
        cmd.append(installer.name)  # In a dry run, use the basename for brevity in output

    if dry_run:
        print(" ".join(cmd))
    else:
        print(f"Importing {pkg.pkg_name!r}")
        p = subprocess.run(cmd, capture_output=True, encoding="utf-8")

        if p.returncode == 0:
            result = pkginfo_file(p.stdout, munki_repo)
            print(f"Imported {pkg.pkg_name!r}")
        else:
            raise MunkiImportException(p)

    return result


def makecatalogs(munki_repo: Path) -> None:
    """Run the makecatalogs utility after importing"""
    cmd = ["/usr/local/munki/makecatalogs", "--repo_url", munki_repo]
    subprocess.run(cmd)