from pathlib import Path

class Replacement:
    def __init__(self, file: Path, offset: int, length: int, replacement_text: str):
        """ Replacement text for file between offset and offset+length.

        @param file: File to replace text in
        @param offset: Offset in file to start text replace
        @param length: Length of text that will be replaced. offset -> offset+length is the section of text to replace.
        @param replacement_text: Text to insert of offset in file.
        """
        self.file = file
        self.offset = offset
        self.length = length
        self.replacement_text = replacement_text

    def toDict(self) -> dict:
        return {"FilePath": self.file.as_posix(),
                "Offset": self.offset,
                "Length": self.length,
                "ReplacementText": self.replacement_text}
