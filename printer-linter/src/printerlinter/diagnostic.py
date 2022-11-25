from pathlib import Path
from typing import Optional, List, Dict, Any

from .replacement import Replacement


class Diagnostic:
    def __init__(self, file: Path, diagnostic_name: str, message: str, level: str, offset: int, replacements: Optional[List[Replacement]] = None) -> None:
        """ A diagnosis of an issue in "file" at "offset" in that file. May include suggested replacements.

        @param file: The path to the file this diagnostic is for.
        @param diagnostic_name: The name of the diagnostic rule that spawned this result. A list can be found in .printer-linter.
        @param message: A message explaining the issue with this file.
        @param level: How important this diagnostic is, ranges from Warning -> Error.
        @param offset: The offset in file where the issue is.
        @param replacements: A list of Replacement that contain replacement text.
        """
        self.file = file
        self.diagnostic_name = diagnostic_name
        self.message = message
        self.offset = offset
        self.level = level
        self.replacements = replacements

    def toDict(self) -> Dict[str, Any]:
        return {"DiagnosticName": self.diagnostic_name,
                "DiagnosticMessage": {
                    "Message": self.message,
                    "FilePath": self.file.as_posix(),
                    "FileOffset": self.offset,
                    "Replacements": [] if self.replacements is None else [r.toDict() for r in self.replacements],
                },
                "Level": self.level
                }
