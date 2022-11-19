class Diagnostic:
    def __init__(self, illness, msg, file, key=None, termination_seq=None):
        self.illness = illness
        self.key = key
        self.msg = msg
        self.file = file
        self._lines = None
        self._location = None
        self._fix = None
        self._content_block = None
        self._termination_seq = termination_seq

    @property
    def location(self):
        if self._location:
            return self._location
        if not self._lines:
            with open(self.file, "r") as f:
                if not self.is_text_file:
                    self._fix = ""
                    return self._fix
                self._lines = f.readlines()

        start_location = {"col": 1, "line": 1}
        end_location = {"col": len(self._lines[-1]) + 1, "line": len(self._lines) + 1}

        if self.key is not None:
            for lino, line in enumerate(self._lines, 1):
                if f'"{self.key}":' in line:
                    col = line.index(f'"{self.key}":') + 1
                    start_location = {"col": col, "line": lino}
                    if self._termination_seq is None:
                        end_location = {"col": len(line) + 1, "line": lino}
                        break
                if f'"{self._termination_seq}":' in line:
                    col = line.index(f'"{self._termination_seq}":') + 1
                    end_location = {"col": col, "line": lino}
        self._location = {"start": start_location, "end": end_location}
        return self._location

    @property
    def is_text_file(self):
        return self.file.name.split(".", maxsplit=1)[-1] in ("def.json", "inst.cfg")

    @property
    def content_block(self):
        if self._content_block:
            return self._content_block

        if not self._lines:
            if not self.is_text_file:
                self._fix = ""
                return self._fix
            with open(self.file, "r") as f:
                self._lines = f.readlines()

        start_line = self.location["start"]["line"]
        start_col = self.location["start"]["col"]
        end_line = self.location["end"]["line"]
        end_col = len(self._lines[start_line:end_line - 1]) + self.location["start"]["col"]
        self._content_block = "".join(self._lines[start_line:end_line])
        return self._content_block

    @property
    def fix(self):
        if self._fix:
            return self._fix

        if not self._lines:
            if not self.is_text_file:
                self._fix = ""
                return self._fix
            with open(self.file, "r") as f:
                self._lines = f.readlines()

        start_line = self.location["start"]["line"]
        start_col = self.location["start"]["col"]
        end_line = self.location["end"]["line"]
        end_col = len(self._lines[start_line:end_line - 1]) + self.location["start"]["col"]
        self._fix = self.content_block[start_col:end_col]
        return self._fix

    def toDict(self):
        diagnostic_dict = {"diagnostic": self.illness, "message": self.msg}
        if self.is_text_file:
            diagnostic_dict |= {"fix": self.fix, "lino": self.location, "content": self.content_block}
        return diagnostic_dict
