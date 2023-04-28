import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Dict

from .formatter import FileFormatter


# Dictionary items with matching keys will be sorted as if they were the value
# Example: "version" will be sorted as if it was "0"
TOP_LEVEL_SORT_PRIORITY = {
    "version":      "0",
    "name":         "1",
    "inherits":     "3",
}

METADATA_SORT_PRIORITY = {
    "visible":      "0",
    "author":       "1",
    "manufacturer": "2",
    "file_formats": "3",
    "platform":     "4",
}

class DefJsonFormatter(FileFormatter):
    def formatFile(self, file: Path):
        """ Format .def.json files according to the rules in settings.

        You can assume that you will be running regex on standard formatted json files, because we load the json first and then
        dump it to a string. This means you only have to write regex that works on the output of json.dump()
        """

        definition = json.loads(file.read_text(), object_pairs_hook=OrderedDict)

        if self._settings["format"].get("format-definition-sort-keys", True) and file.stem.split(".")[0] != "fdmprinter":
            definition = self.order_keys(definition)

        content = json.dumps(definition, indent=self._settings["format"].get("format-definition-indent", 4))

        if self._settings["format"].get("format-definition-bracket-newline", True):
            newline = re.compile(r"(\B\s+)(\"[\w\"]+)(\:\s\{)")
            content = newline.sub(r"\1\2:\1{", content)

        if self._settings["format"].get("format-definition-single-value-single-line", True):
            single_value_dict = re.compile(r"(:)(\s*\n?.*\{\s+)(\".*)(\d*\s*\})(.*\n,?)")
            content = single_value_dict.sub(r"\1 { \3 }\5", content)

            single_value_list = re.compile(r"(:)(\s*\n?.*\[\s+)(\".*)(\d*\s*\])(.*\n,?)")
            content = single_value_list.sub(r"\1 [ \3 ]\5", content)

        if self._settings["format"].get("format-definition-paired-coordinate-array", True):
            paired_coordinates = re.compile(r"(\s*\[)\s*([-\d\.]+),\s*([-\d\.]+)[\s]*(\])")
            content = paired_coordinates.sub(r"\1\2, \3\4", content)

        file.write_text(content)

    def order_keys(self, json_content: OrderedDict) -> OrderedDict:
        """ Orders json keys lexicographically """
        # First order all keys (Recursive) lexicographically
        json_content_text = json.dumps(json_content, sort_keys=True)
        json_content = json.loads(json_content_text, object_pairs_hook=OrderedDict)

        # Do a custom ordered sort on the top level items in the json. This is so that keys like "version" appear at the top.
        json_content = self.custom_sort_keys(json_content, TOP_LEVEL_SORT_PRIORITY)

        # Do a custom ordered sort on collections that are one level deep into the json
        if "metadata" in json_content.keys():
            json_content["metadata"] = self.custom_sort_keys(json_content["metadata"], METADATA_SORT_PRIORITY)

        return json_content


    def custom_sort_keys(self, ordered_dictionary: OrderedDict, sort_priority: Dict[str, str]) -> OrderedDict:
        """ Orders keys in dictionary lexicographically, except for keys with matching strings in sort_priority.

        Keys in ordered_dictionary that match keys in sort_priority will sort based on the value in sort_priority.

        @param ordered_dictionary: A dictionary that will have it's top level keys sorted
        @param sort_priority: A mapping from string keys to alternative strings to be used instead when sorting.
        @return: A dictionary sorted by it's top level keys
        """
        return OrderedDict(sorted(ordered_dictionary.items(), key=lambda x: sort_priority[x[0]] if str(x[0]) in sort_priority.keys() else str(x[0])))
