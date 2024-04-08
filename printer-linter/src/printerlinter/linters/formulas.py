import difflib
import json
import re
from pathlib import Path
from typing import Iterator


from cura.Settings.CuraFormulaFunctions import CuraFormulaFunctions
from ..diagnostic import Diagnostic
from .linter import Linter
from configparser import ConfigParser

class Formulas(Linter):
    """ Finds issues in definition files, such as overriding default parameters """
    def __init__(self, file: Path, settings: dict) -> None:
        super().__init__(file, settings)
        self._cura_formula_functions = CuraFormulaFunctions(self)
        self._correct_formulas = ["extruderValue", "extruderValues", "anyExtruderWithMaterial", "anyExtruderNrWithOrDefault"
                              , "resolveOrValue", "defaultExtruderPosition", "valueFromContainer", "extruderValueFromContainer"]
        self._definition = {}

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
                                 message=f"Given formula {value_dict} to calulate {key} of seems incorrect, Do you mean {self._correct_formula}? please correct the formula and try again.",
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
        self._correct_formula = self._correctFormula(formula)
        if self._correct_formula == formula:
            return False
        else:
            return True

    def _correctFormula(self, input_sentence: str) -> str:
        # Find all alphanumeric words, '()' and content inside them, and punctuation
        chunks = re.split(r'(\(.*?\))', input_sentence)  # split input by parentheses

        corrected_chunks = []
        for chunk in chunks:
            if chunk.startswith('(') and chunk.endswith(')'):  # if chunk is a formula in parentheses
                corrected_chunks.append(chunk)  # leave it as is
            else:  # if chunk is outside parentheses
                words = re.findall(r'\w+', chunk)  # find potential function names
                for word in words:
                    if difflib.get_close_matches(word, self._correct_formulas, n=1,cutoff=0.6):  # if there's a close match in correct formulas
                        chunk = chunk.replace(word, difflib.get_close_matches(word, self._correct_formulas, n=1, cutoff=0.6)[0])  # replace it
                corrected_chunks.append(chunk)

        return ''.join(corrected_chunks)  # join chunks back together
