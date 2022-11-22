class Diagnostic:
    def __init__(self, file, diagnostic_name, message, level, offset, replacements=None) -> None:
        self.file = file
        self.diagnostic_name = diagnostic_name
        self.message = message
        self.offset = offset
        self.level = level
        self.replacements = replacements

    def toDict(self) -> dict:
        diagnostic_dict = {"DiagnosticName": self.diagnostic_name,
                           "DiagnosticMessage": {
                               "Message": self.message,
                               "FilePath": self.file.as_posix(),
                               "FileOffset": self.offset,
                               "Replacements": [] if self.replacements is None else [r.toDict() for r in self.replacements],
                           },
                           "Level": self.level
                           }
        return diagnostic_dict
