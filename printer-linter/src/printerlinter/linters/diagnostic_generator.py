from abc import ABC, abstractmethod
from typing import Iterator

from ..diagnostic import Diagnostic


class DiagnosticGenerator(ABC):
    def __init__(self, file, settings) -> None:
        self._settings = settings
        self._file = file

    @abstractmethod
    def check(self) -> Iterator[Diagnostic]:
        pass