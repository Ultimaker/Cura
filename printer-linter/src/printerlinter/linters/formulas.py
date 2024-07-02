import difflib
import json
import os
import re
from configparser import ConfigParser
from pathlib import Path
from typing import Iterator

from ..diagnostic import Diagnostic
from ..replacement import Replacement
from .linter import Linter

FORMULA_NAMES = [
    "extruderValue",
    "extruderValues",
    "anyExtruderWithMaterial",
    "anyExtruderNrWithOrDefault",
    "resolveOrValue",
    "defaultExtruderPosition",
    "valueFromContainer",
    "extruderValueFromContainer",
    "math",
    "round",
    "max",
    "ceil",
    "min",
    "sqrt",
    "log",
    "tan",
    "cos",
    "sin",
    "atan",
    "acos",
    "asin",
    "floor",
    "sum",
    "len",
    "radians",
    "degrees"
]

DELIMITERS = [r'\+', '-', '=', '/', '\*', r'\(', r'\)', r'\[', r'\]', '{', '}', ' ', '^']


class Formulas(Linter):
    """Finds Typos in the definition files and their formulas."""

    def __init__(self, file: Path, settings: dict) -> None:
        super().__init__(file, settings)
        self._cura_correction_strings = FORMULA_NAMES + list(self.getCuraSettingList())
        self._definition = {}

    def getCuraSettingList(self) -> list:
        settings_list = []

        with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources", "definitions", "fdmprinter.def.json")) as data:
            json_data = json.load(data)
        settings_list += self.extractKeys(json_data)

        with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources", "definitions", "fdmextruder.def.json")) as data:
            json_data = json.load(data)
        settings_list += self.extractKeys(json_data)

        return settings_list

    def extractKeys(self, json_obj, parent_key=''):
        keys_with_value = []
        for key, values in json_obj.items():
            new_key = key
            if isinstance(values, dict):
                if 'label' in values:
                    keys_with_value.append(new_key)
                keys_with_value.extend(self.extractKeys(values, new_key))
        return keys_with_value

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
                    if value in ("enable", "resolve", "value", "minimum_value_warning", "maximum_value_warning",
                            "maximum_value", "minimum_value"):
                        key_incorrect = self.checkValueIncorrect(key)
                        if key_incorrect:
                            found = self._appendCorrections(key, key)
                        value_incorrect = self.checkValueIncorrect(value_dict[value])
                        if value_incorrect:
                            found = self._appendCorrections(key, value_dict[value])
                        if key_incorrect or value_incorrect:

                            if len(found.group().splitlines()) > 1:
                                replacements = []
                            else:
                                replacements = [Replacement(
                                    file=self._file,
                                    offset=found.span(1)[0],
                                    length=len(found.group()),
                                    replacement_text=self._replacement_text)]
                            yield Diagnostic(
                                file=self._file,
                                diagnostic_name="diagnostic-incorrect-formula",
                                message=f"Given formula {found.group()} seems incorrect, Do you mean {self._correct_formula}? please correct the formula and try again.",
                                level="Error",
                                offset=found.span(0)[0],
                                replacements=replacements
                            )

        yield

    def _appendCorrections(self, key, incorrectString):

        if self._file.suffix == '.cfg':
            key_with_incorrectValue = re.compile(r'(\b' + key + r'\b\s*=\s*[^=\n]+.*)')
        else:
            key_with_incorrectValue = re.compile(r'.*(\"' + key + r'\"[\s\:\S]*?)\{[\s\S]*?\},?')
        found = key_with_incorrectValue.search(self._content)
        if len(found.group().splitlines()) > 1:
            self._replacement_text = ''
        else:
            self._replacement_text = found.group().replace(incorrectString, self._correct_formula).strip(' ')
        return found


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
            if config.has_section(section):
                options = config.options(section)
                for option in options:
                    values ={}
                    values["value"] = config.get(section, option)
                    overrides[option] = values
                file_data["overrides"]= overrides# Process the value here

        return file_data

    def checkValueIncorrect(self, formula) -> bool:
        if isinstance(formula, str):
            self._correct_formula = self._correctTyposInFormula(formula)
            return self._correct_formula != formula
        else:
            return False

    def _correctTyposInFormula(self, formula):
        pattern = '|'.join(DELIMITERS)
        tokens = re.split(pattern, formula)

        output = formula
        for token in tokens:
            if '(' not in token and ')' not in token:
                cleaned_token = re.sub(r'[^\w\s]', '', token)
                possible_matches = difflib.get_close_matches(cleaned_token, self._cura_correction_strings, n=1, cutoff=0.8)
                if possible_matches:
                    output = output.replace(cleaned_token, possible_matches[0])
        return output

