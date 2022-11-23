from pathlib import Path
from typing import Optional

from .linters.profile import Profile
from .linters.defintion import Definition
from .linters.diagnostic_generator import DiagnosticGenerator
from .linters.meshes import Meshes


def create(file: Path, settings) -> Optional[DiagnosticGenerator]:
    """ Returns a DiagnosticGenerator depending on the file format """
    if not file.exists():
        return None
    elif ".inst" in file.suffixes and ".cfg" in file.suffixes:
        return Profile(file, settings)
    elif ".def" in file.suffixes and ".json" in file.suffixes:
        if file.stem in ("fdmprinter.def", "fdmextruder.def"):
            return None
        return Definition(file, settings)
    elif file.parent.stem == "meshes":
        return Meshes(file, settings)

    return None
