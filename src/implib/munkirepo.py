"""munki repo"""
import plistlib
import sys

from pathlib import Path
from typing import Any, Dict


class MunkiImportPreferences:
    """munkiimport preferences"""
    def __init__(self, domain: str = "com.googlecode.munki.munkiimport.plist") -> None:
        self.domain = domain
        self._preferences = self.read_preferences()

    def find_preference_file(self) -> Path:
        """Find the munkiimport preference file, preferring user domain over system domain"""
        user = Path("~/Library/Preferences").expanduser().joinpath(self.domain)
        system = Path("/Library/Preferences").joinpath(self.domain)
        configure_munkiimport = "munkiimport --configure"

        if not user.exists() or system.exists() and not user.exists() and not system.exists():
            message = (f"Could not find preference files at either:\n - {str(user)!r}\n - {str(system)!r}\n"
                       f"Please run {configure_munkiimport!r} and set values for the repo URL and"
                       " pkginfo extension.")

            print(message, file=sys.stderr)
            sys.exit(2)

        return user if user.exists() else system

    def read_preferences(self) -> Dict[Any, Any]:
        """Read the munkiimport preference file"""
        preference_file = self.find_preference_file()

        with open(preference_file, 'rb') as f:
            return plistlib.load(f)

    @property
    def repo_url(self) -> Path:
        """repo_url from preference file"""
        return Path(self._preferences.get("repo_url", "file:///Volumes/munki_repo"))

    @property
    def pkginfo_extension(self) -> str:
        """pkginfo_extension from preference file"""
        return self._preferences.get("pkginfo_extension", ".plist")

    @property
    def pkgsinfo_directory(self) -> Path:
        """pkgsinfo path from repo_url"""
        return self.repo_url.joinpath("pkgsinfo")

    @property
    def icon_directory(self) -> Path:
        """icon directory from repo_url"""
        return self.repo_url.joinpath("icons")
