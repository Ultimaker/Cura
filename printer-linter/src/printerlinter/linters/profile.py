from typing import Iterator

from ..diagnostic import Diagnostic
from .linter import Linter


class Profile(Linter):
    def check(self) -> Iterator[Diagnostic]:
        yield
