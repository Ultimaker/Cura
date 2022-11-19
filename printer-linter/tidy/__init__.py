from .defintion import Definition
from .diagnostic import Diagnostic
from .meshes import Meshes
from .profile import Profile

__all__ = ["Profile", "Definition", "Meshes", "Diagnostic", "create"]


def create(file, settings):
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
