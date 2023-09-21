from pathlib import Path
from typing import Iterator

from ..diagnostic import Diagnostic
from .linter import Linter


class Directory(Linter):
    def __init__(self, file: Path, settings: dict) -> None:
        """ Finds issues in the parent directory"""
        super().__init__(file, settings)

    def check(self) -> Iterator[Diagnostic]:
        if self._settings["checks"].get("diagnostic-resources-macos-app-directory-name", False):
            for check in self.checkForDotInDirName():
                yield check

        yield

    def checkForDotInDirName(self) -> Iterator[Diagnostic]:
        """ Check if there is a dot in the directory name, MacOS has trouble signing and notarizing otherwise """
        if any("." in p for p in self._file.parent.parts):
            yield Diagnostic(
                file = self._file,
                diagnostic_name = "diagnostic-resources-macos-app-directory-name",
                message = f"Directory name containing a `.` not allowed {self._file.suffix}, rename directory containing this file e.q: `_`",
                level = "Error",
                offset = 1
            )
        yield

