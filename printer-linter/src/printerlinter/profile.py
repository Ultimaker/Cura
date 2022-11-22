class Profile:
    def __init__(self, file, settings) -> None:
        self._settings = settings
        self._file = file

    def check(self) -> None:
        yield
