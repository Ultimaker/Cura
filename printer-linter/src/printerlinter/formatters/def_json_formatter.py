import json
import re
from pathlib import Path

from .formatter import FileFormatter

class DefJsonFormatter(FileFormatter):
    def format(self, file: Path):
        """ Format .def.json files according to the rules in settings """
        definition = json.loads(file.read_text())
        content = json.dumps(definition, indent=self._settings["format"].get("format-definition-indent", 4),
                             sort_keys=self._settings["format"].get("format-definition-sort-keys", True))

        if self._settings["format"].get("format-definition-bracket-newline", True):
            newline = re.compile(r"(\B\s+)(\"[\w\"]+)(\:\s\{)")
            content = newline.sub(r"\1\2:\1{", content)

        if self._settings["format"].get("format-definition-single-value-single-line", True):
            single_value_dict = re.compile(r"(:)(\s*\n?.*\{\s+)(\".*)(\d*\s*\})(\s*)(,?)")
            content = single_value_dict.sub(r"\1 { \3 }\6", content)

            single_value_list = re.compile(r"(:)(\s*\n?.*\[\s+)(\".*)(\d*\s*\])(\s*)(,?)")
            content = single_value_list.sub(r"\1 [ \3 ]\6", content)

        if self._settings["format"].get("format-definition-paired-coordinate-array", True):
            paired_coordinates = re.compile(r"(\[)\s+(-?\d*),\s*(-?\d*)\s*(\])")
            content = paired_coordinates.sub(r"\1 \2, \3 \4", content)

        file.write_text(content)