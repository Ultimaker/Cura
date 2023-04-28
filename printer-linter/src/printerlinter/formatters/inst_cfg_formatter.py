import configparser
import json
import re
from collections import OrderedDict
from pathlib import Path

from .formatter import FileFormatter

class InstCfgFormatter(FileFormatter):
    def formatFile(self, file: Path):
        """ Format .inst.cfg files according to the rules in settings """
        config = configparser.ConfigParser()
        config.read(file)

        if self._settings["format"].get("format-profile-sort-keys", True):
            for section in config._sections:
                config._sections[section] = OrderedDict(sorted(config._sections[section].items(), key=lambda t: t[0]))
            config._sections = OrderedDict(sorted(config._sections.items(), key=lambda t: t[0]))

        with open(file, "w") as f:
            config.write(f, space_around_delimiters=self._settings["format"].get("format-profile-space-around-delimiters", True))