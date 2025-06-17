from pathlib import Path
from typing import Optional, List

from .linters.profile import Profile
from .linters.defintion import Definition
from .linters.linter import Linter
from .linters.meshes import Meshes
from .linters.directory import Directory
from .linters.formulas import Formulas


def getLinter(file: Path, settings: dict) -> Optional[List[Linter]]:
    """ Returns a Linter depending on the file format """
    if not file.exists():
        return [Directory(file, settings)]

    if ".inst" in file.suffixes and file.suffixes[-1] == ".cfg":
        return [Directory(file, settings), Profile(file, settings), Formulas(file, settings)]

    if ".def" in file.suffixes and file.suffixes[-1] == ".json":
        if file.stem in ("fdmprinter.def", "fdmextruder.def"):
            return  [Formulas(file, settings)]
        return [Directory(file, settings), Definition(file, settings), Formulas(file, settings)]

    if file.parent.stem == "meshes":
        return [Meshes(file, settings)]

    return [Directory(file, settings)]
