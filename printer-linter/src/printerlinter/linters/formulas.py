import json
import os
from pathlib import Path
from typing import Iterator

from UM.VersionUpgradeManager import VersionUpgradeManager
from unittest.mock import MagicMock
from ..diagnostic import Diagnostic
from .linter import Linter
from configparser import ConfigParser
from cura.CuraApplication import CuraApplication  # To compare against the current SettingVersion.
from UM.Settings.DefinitionContainer import DefinitionContainer

class Formulas(Linter):
    """ Finds issues in definition files, such as overriding default parameters """
    def __init__(self, file: Path, settings: dict) -> None:
        super().__init__(file, settings)
        self._all_keys = self.collectAllSettingIds()
        self._definition = {}

    def collectAllSettingIds(self):
        VersionUpgradeManager._VersionUpgradeManager__instance = VersionUpgradeManager(MagicMock())
        CuraApplication._initializeSettingDefinitions()
        definition_container = DefinitionContainer("whatever")
        with open(os.path.join(os.path.dirname(__file__), "..", "..","..","..", "resources", "definitions", "fdmprinter.def.json"),
                encoding="utf-8") as data:
            definition_container.deserialize(data.read())
        return definition_container.getAllKeys()

    def check(self) -> Iterator[Diagnostic]:
        if self._settings["checks"].get("diagnostic-incorrect-formula", False):
            for check in self.checkFormulas():
                yield check

        yield

    def checkFormulas(self) -> Iterator[Diagnostic]:

        self._loadDefinitionFiles(self._file)
        self._content = self._file.read_text()
        definition_name = list(self._definition.keys())[0]
        definition = self._definition[definition_name]
        if "overrides" in definition:
            for key, value_dict in definition["overrides"].items():
                for value in value_dict:
                    if value in ("enable", "resolve", "value", "minimum_value_warning", "maximum_value_warning", "maximum_value", "minimum_value"):
                         value_incorrect = self.checkValueIncorrect(value_dict[value].strip("="))
                         if value_incorrect:

                             yield Diagnostic(
                                 file=self._file,
                                 diagnostic_name="diagnostic-incorrect-formula",
                                 message=f"Given formula {value_dict} to calulate {key} of seems incorrect, please correct the formula and try again.",
                                 level="Error",
                                 offset=1
                             )
        yield

    def _loadDefinitionFiles(self, definition_file) -> None:
        """ Loads definition file contents into self._definition. Also load parent definition if it exists. """
        definition_name = Path(definition_file.stem).stem

        if not definition_file.exists() or definition_name in self._definition:
            return

        if definition_file.suffix == ".json":
            # Load definition file into dictionary
            self._definition[definition_name] = json.loads(definition_file.read_text())

        if definition_file.suffix == ".cfg":
            self._definition[definition_name] = self._parseCfg(definition_file)


    def _parseCfg(self, file_path:Path) -> dict:
        config = ConfigParser()
        config.read([file_path])
        file_data  ={}
        overrides = {}

        available_sections = ["values"]
        for section in available_sections:
            options = config.options(section)
            for option in options:
                values ={}
                values["value"] = config.get(section, option)
                overrides[option] = values
            file_data["overrides"]= overrides# Process the value here

        return file_data

    def checkValueIncorrect(self, formula:str) -> bool:
        try:
            compiled_formula = compile(formula, "", "eval")
        except SyntaxError:
            return True
        return False
