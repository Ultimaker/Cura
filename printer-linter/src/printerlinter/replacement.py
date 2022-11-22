class Replacement:
    def __init__(self, file, offset, length, replacement_text):
        self.file = file
        self.offset = offset
        self.length = length
        self.replacement_text = replacement_text

    def toDict(self) -> dict:
        return {"FilePath": self.file.as_posix(),
                "Offset": self.offset,
                "Length": self.length,
                "ReplacementText": self.replacement_text}
