# Copyright (c) 2024 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Iterator

from ..diagnostic import Diagnostic
from .linter import Linter


class Profile(Linter):
    def check(self) -> Iterator[Diagnostic]:
        yield
