from pathlib import Path
from typing import Optional, List

from .linters.profile import Profile
from .linters.defintion import Definition
from .linters.linter import Linter
from .linters.meshes import Meshes
from .linters.directory import Directory


def getLinter(file: Path, settings: dict) -> Optional[List[Linter]]:
    """ Returns a Linter depending on the file format """
    if not file.exists():
        return None

    if ".inst" in file.suffixes and ".cfg" in file.suffixes:
        return [Directory(file, settings), Profile(file, settings)]

    if ".def" in file.suffixes and ".json" in file.suffixes:
        if file.stem in ("fdmprinter.def", "fdmextruder.def"):
            return None
        return [Directory(file, settings), Definition(file, settings)]

    if file.parent.stem == "meshes":
        return [Meshes(file, settings)]

    return [Directory(file, settings)]
