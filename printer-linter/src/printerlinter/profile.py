class Profile:
    def __init__(self, file, settings):
        self._settings = settings
        self._file = file

    def check(self):
        yield
