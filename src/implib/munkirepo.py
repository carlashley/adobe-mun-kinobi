"""munki repo"""
import plistlib
import sys

from pathlib import Path
from typing import Any, Dict


class MunkiImportPreferences:
    """munkiimport preferences"""
    def __init__(self, domain: str = "com.googlecode.munki.munkiimport.plist") -> None:
        self.domain = domain
        self.user = Path("~/Library/Preferences").expanduser().joinpath(self.domain)
        self.system = Path("/Library/Preferences").joinpath(self.domain)

    def find_preference_file(self) -> Path:
        """Find the munkiimport preference file, preferring user domain over system domain"""
        return self.user if self.user.exists() else self.system

    def read_preferences(self) -> Dict[Any, Any]:
        """Read the munkiimport preference file"""
        preference_file = self.find_preference_file()

        try:
            with open(preference_file, 'rb') as f:
                return plistlib.load(f)
        except FileNotFoundError:
            configure_munkiimport = "munkiimport --configure"
            message = (f"Could not find preference files at either:\n - {str(self.user)!r}\n - {str(self.system)!r}\n"
                       f"Please run {configure_munkiimport!r} and set values for the repo URL and"
                       " pkginfo extension.")

            print(message, file=sys.stderr)
            sys.exit(2)

    @property
    def repo_url(self) -> Path:
        """repo_url from preference file"""
        prefs = self.read_preferences()
        repo_url = prefs.get("repo_url", "file:///Volumes/munki_repo")
        return Path(repo_url)

    @property
    def pkginfo_extension(self) -> str:
        """pkginfo_extension from preference file"""
        prefs = self.read_preferences()
        return prefs.get("pkginfo_extension", ".plist")

    @property
    def pkgsinfo_directory(self) -> Path:
        """pkgsinfo path from repo_url"""
        return self.repo_url.joinpath("pkgsinfo")

    @property
    def icon_directory(self) -> Path:
        """icon directory from repo_url"""
        return self.repo_url.joinpath("icons")
