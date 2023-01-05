from abc import ABC, abstractmethod
from pathlib import Path


class FileFormatter(ABC):
    def __init__(self, settings: dict) -> None:
        """ Yields Diagnostics for file, these are issues with the file such as bad text format or too large file size.

        @param file: A file to generate diagnostics for
        @param settings: A list of settings containing rules for creating diagnostics
        """
        self._settings = settings

    @abstractmethod
    def formatFile(self, file: Path) -> None:
        pass