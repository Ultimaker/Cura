from pathlib import Path
from typing import Iterator

from ..diagnostic import Diagnostic, GitComment
from .linter import Linter


class Directory(Linter):
    def __init__(self, file: Path, settings: dict) -> None:
        """ Finds issues in the parent directory"""
        super().__init__(file, settings)

    def check(self) -> Iterator[Diagnostic]:
        if self._file.exists() and self._settings["checks"].get("diagnostic-resources-macos-app-directory-name", False):
            for check in self.checkForDotInDirName():
                yield check
        elif self._settings["checks"].get("diagnostic-resource-file-deleted", False):
            for check in self.checkFilesDeleted():
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

    def checkFilesDeleted(self) -> Iterator[GitComment]:
        if not self._file.exists():
            """ Check if there is a file that is deleted, this causes upgrade scripts to not work properly """
            yield GitComment( f'File: **{self._file}** must not be deleted as it is not allowed. It will create issues upgrading Cura' )
        yield