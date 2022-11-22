from typing import Iterator

from ..diagnostic import Diagnostic
from .diagnostic_generator import DiagnosticGenerator


class Profile(DiagnosticGenerator):
    def check(self) -> Iterator[Diagnostic]:
        yield
