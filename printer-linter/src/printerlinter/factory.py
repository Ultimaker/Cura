from pathlib import Path
from typing import Optional

from .linters.profile import Profile
from .linters.defintion import Definition
from .linters.linter import Linter
from .linters.meshes import Meshes


def getLinter(file: Path, settings: dict) -> Optional[Linter]:
    """ Returns a Linter depending on the file format """
    if not file.exists():
        return None

    if ".inst" in file.suffixes and ".cfg" in file.suffixes:
        return Profile(file, settings)

    if ".def" in file.suffixes and ".json" in file.suffixes:
        if file.stem in ("fdmprinter.def", "fdmextruder.def"):
            return None
        return Definition(file, settings)

    if file.parent.stem == "meshes":
        return Meshes(file, settings)

    return None
