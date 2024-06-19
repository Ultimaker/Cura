import json
import re
from pathlib import Path
from typing import Iterator

from ..diagnostic import Diagnostic
from .linter import Linter
from ..replacement import Replacement


class Definition(Linter):
    """ Finds issues in definition files, such as overriding default parameters """
    def __init__(self, file: Path, settings: dict) -> None:
        super().__init__(file, settings)
        self._definitions = {}
        self._definition_name = None
        self._experimental_settings = []
        self._loadDefinitionFiles(file)
        self._content = self._file.read_text()
        self._loadExperimentalSettings()
        self._loadBasePrinterSettings()

    @property
    def base_def(self):
        if "fdmextruder" in self._definitions:
            return "fdmextruder"
        return "fdmprinter"

    def check(self) -> Iterator[Diagnostic]:
        if self._settings["checks"].get("diagnostic-definition-redundant-override", False):
            for check in self.checkRedefineOverride():
                yield check

        if self._settings["checks"].get("diagnostic-material-temperature-defined", False):
            for check in self.checkMaterialTemperature():
                yield check

        if self._settings["checks"].get("diagnostic-definition-experimental-setting", False):
            for check in self.checkExperimentalSetting():
                yield check

        # Add other which will yield Diagnostic's
        # TODO: A check to determine if the user set value is with the min and max value defined in the parent and doesn't trigger a warning
        # TODO: A check if the key exist in the first place
        # TODO: Check if the model platform exist

        yield

    def checkRedefineOverride(self) -> Iterator[Diagnostic]:
        """ Checks if definition file overrides its parents settings with the same value. """
        definition = self._definitions[self._definition_name]
        if "overrides" in definition and self._definition_name not in ("fdmprinter", "fdmextruder"):
            for key, value_dict in definition["overrides"].items():
                is_redefined, child_key, child_value, parent, inherited_by= self._isDefinedInParent(key, value_dict, definition['inherits'])
                if is_redefined:
                    redefined = re.compile(r'.*(\"' + key + r'\"[\s\:\S]*?)\{[\s\S]*?\},?')
                    found = redefined.search(self._content)
                    # TODO: Figure out a way to support multiline fixes in the PR review GH Action, for now suggest no fix to ensure no ill-formed json are created
                    #  see: https://github.com/platisd/clang-tidy-pr-comments/issues/37
                    if len(found.group().splitlines()) > 1:
                        replacements = []
                    else:
                        replacements = [Replacement(
                            file = self._file,
                            offset = found.span(1)[0],
                            length = len(found.group()),
                            replacement_text = "")]

                    yield Diagnostic(
                        file = self._file,
                        diagnostic_name = "diagnostic-definition-redundant-override",
                        message = f"Overriding {key} with the same value ({child_key}: {child_value}) as defined in parent definition: {inherited_by}",
                        level = "Warning",
                        offset = found.span(0)[0],
                        replacements = replacements
                    )

    def checkMaterialTemperature(self) -> Iterator[Diagnostic]:
        """Checks if definition file has material tremperature defined within them"""
        definition = self._definitions[self._definition_name]
        if "overrides" in definition and self._definition_name not in ("fdmprinter", "fdmextruder"):
            for key, value_dict in definition["overrides"].items():
                if "temperature" in key and "material" in key:

                    redefined = re.compile(r'.*(\"' + key + r'\"[\s\:\S]*?)\{[\s\S]*?\},?')
                    found = redefined.search(self._content)
                    if len(found.group().splitlines()) > 1:
                        replacements = []
                    else:
                        replacements = [Replacement(
                            file=self._file,
                            offset=found.span(1)[0],
                            length=len(found.group()),
                            replacement_text="")]

                    yield Diagnostic(
                        file=self._file,
                        diagnostic_name="diagnostic-material-temperature-defined",
                        message=f"Overriding {key} as it belongs to material temperature catagory and shouldn't be placed in machine definitions",
                        level="Warning",
                        offset=found.span(0)[0],
                        replacements=replacements
                    )

    def checkExperimentalSetting(self) -> Iterator[Diagnostic]:
        """Checks if definition uses experimental settings"""
        definition = self._definitions[self._definition_name]
        if "overrides" in definition and self._definition_name not in ("fdmprinter", "fdmextruder"):
            for setting in definition["overrides"]:
                if setting in self._experimental_settings:
                    redefined = re.compile(setting)
                    found = redefined.search(self._content)
                    yield Diagnostic(
                        file=self._file,
                        diagnostic_name="diagnostic-definition-experimental-setting",
                        message=f"Setting {setting} is still experimental and should not be used in default profiles",
                        level="Warning",
                        offset=found.span(0)[0]
                    )

    def _loadDefinitionFiles(self, definition_file) -> None:
        """ Loads definition file contents into self._definitions. Also load parent definition if it exists. """
        definition_name = Path(definition_file.stem).stem

        if not definition_file.exists() or definition_name in self._definitions:
            return

        if self._definition_name is None:
            self._definition_name = definition_name

        # Load definition file into dictionary
        self._definitions[definition_name] = json.loads(definition_file.read_text())

        # Load parent definition if it exists
        if "inherits" in self._definitions[definition_name]:
            if self._definitions[definition_name]['inherits'] in ("fdmextruder", "fdmprinter"):
                parent_file = definition_file.parent.parent.joinpath("definitions", f"{self._definitions[definition_name]['inherits']}.def.json")
            else:
                parent_file = definition_file.parent.joinpath(f"{self._definitions[definition_name]['inherits']}.def.json")
            self._loadDefinitionFiles(parent_file)

    def _isDefinedInParent(self, key, value_dict, inherits_from):
        if self._ignore(key, "diagnostic-definition-redundant-override"):
            return False, None, None, None, None
        if "overrides" not in self._definitions[inherits_from]:
            return self._isDefinedInParent(key, value_dict, self._definitions[inherits_from]["inherits"])

        parent = self._definitions[inherits_from]["overrides"]
        if key not in self._definitions[self.base_def]["overrides"]:
            is_number = False
        else:
            is_number = self._definitions[self.base_def]["overrides"][key]["type"] in ("float", "int")
        for child_key, child_value in value_dict.items():
            if key in parent:
                if child_key in ("default_value", "value"):
                    check_values = [cv for cv in [parent[key].get("default_value", None), parent[key].get("value", None)] if cv is not None]
                else:
                    check_values = [parent[key].get(child_key, None)]
                for check_value in check_values:
                    if is_number and child_key in ("default_value", "value"):
                        try:
                            v = str(float(child_value))
                        except:
                            v = child_value
                        try:
                            cv = str(float(check_value))
                        except:
                            cv = check_value
                    else:
                        v = child_value
                        cv = check_value
                    if v == cv:
                        return True, child_key, child_value, parent, inherits_from

                if "inherits" in parent:
                    return self._isDefinedInParent(key, value_dict, parent["inherits"])
        return False, None, None, None, None

    def _loadExperimentalSettings(self):
        try:
            self._experimental_settings = self._definitions[self.base_def]["settings"]["experimental"]["children"].keys()
        except:
            pass

    def _loadBasePrinterSettings(self):
        settings = {}
        for k, v in self._definitions[self.base_def]["settings"].items():
            self._getSetting(k, v, settings)
        self._definitions[self.base_def] = {"overrides": settings}

    def _getSetting(self, name, setting, settings) -> None:
        if "children" in setting:
            for childname, child in setting["children"].items():
                self._getSetting(childname, child, settings)
        settings |= {name: setting}

    def _ignore(self, key: dict, type_of_check: str) -> bool:
        if f"{type_of_check}-ignore" in self._settings:
            filters = [re.compile(f) for f in self._settings[f"{type_of_check}-ignore"]]
            for f in filters:
                if f.match(key):
                    return True
        return False
