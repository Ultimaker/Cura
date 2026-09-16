import re
from typing import Iterator, Tuple

from ..diagnostic import Diagnostic
from .linter import Linter
from pathlib import Path
from configparser import ConfigParser

class Profile(Linter):
    MAX_SIZE_OF_NAME = 20
    def __init__(self, file: Path, settings: dict) -> None:
        """ Finds issues in the parent directory"""
        super().__init__(file, settings)
        self._content = self._file.read_text()


    def check(self) -> Iterator[Diagnostic]:
        if self._file.exists() and self._settings["checks"].get("diagnostic-long-profile-names", False):
            for check in self.checklengthofProfileName():
                yield check


    def checklengthofProfileName(self) -> Iterator[Diagnostic]:

        """ check the name of profile and where it is found"""
        name_of_profile, found = self._getprofileName()
        if len(name_of_profile) > Profile.MAX_SIZE_OF_NAME:
            yield Diagnostic(
                file=self._file,
                diagnostic_name="diagnostic-long-profile-names",
                message = f"The profile name **{name_of_profile}** exceeds the maximum length limit. For optimal results, please limit it to 20 characters or fewer.",
                level="Warning",
                offset = found.span(0)[0]
            )

    def _getprofileName(self) -> Tuple[str, bool]:
        config = ConfigParser()
        config.read([self._file])
        name_of_profile = config.get("general", "name")
        redefined = re.compile(re.escape(name_of_profile))
        found = redefined.search(self._content)
        return name_of_profile, found
