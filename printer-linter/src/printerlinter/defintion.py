import json
import re
from pathlib import Path

from .diagnostic import Diagnostic
from .replacement import Replacement


class Definition:
    def __init__(self, file, settings) -> None:
        self._settings = settings
        self._file = file
        self._defs = {}
        self._getDefs(file)

        self._content = self._file.read_text()

        settings = {}
        for k, v in self._defs["fdmprinter"]["settings"].items():
            self._getSetting(k, v, settings)
        self._defs["fdmprinter"] = {"overrides": settings}

    def check(self) -> None:
        if self._settings["checks"].get("diagnostic-definition-redundant-override", False):
            for check in self.checkRedefineOverride():
                yield check

        # Add other which will yield Diagnostic's
        # TODO: A check to determine if the user set value is with the min and max value defined in the parent and doesn't trigger a warning
        # TODO: A check if the key exist in the first place
        # TODO: Check if the model platform exist

        yield

    def checkRedefineOverride(self) -> None:
        definition_name = list(self._defs.keys())[0]
        definition = self._defs[definition_name]
        if "overrides" in definition and definition_name != "fdmprinter":
            for key, value_dict in definition["overrides"].items():
                is_redefined, value, parent = self._isDefinedInParent(key, value_dict, definition['inherits'])
                if is_redefined:
                    redefined = re.compile(r'.*(\"' + key + r'\"[\s\S]*?\{)[\s\S]*?(\}[,\"]?)')
                    found = redefined.search(self._content)
                    yield Diagnostic(
                        file = self._file,
                        diagnostic_name = "diagnostic-definition-redundant-override",
                        message = f"Overriding {key} with the same value ({value}) as defined in parent definition: {definition['inherits']}",
                        level = "Warning",
                        offset = found.span(0)[0],
                        replacements = [Replacement(
                            file = self._file,
                            offset = found.span(1)[0],
                            length = found.span(2)[1] - found.span(1)[0],
                            replacement_text = "")]
                    )

    def checkValueOutOfBounds(self) -> None:
        pass

    def _getSetting(self, name, setting, settings) -> None:
        if "children" in setting:
            for childname, child in setting["children"].items():
                self._getSetting(childname, child, settings)
        settings |= {name: setting}

    def _getDefs(self, file) -> None:
        """ Loads up file, and it's parent definitions into self._defs """
        if not file.exists() or Path(file.stem).stem in self._defs:
            return
        self._defs[Path(file.stem).stem] = json.loads(file.read_text())
        if "inherits" in self._defs[Path(file.stem).stem]:
            parent_file = file.parent.joinpath(f"{self._defs[Path(file.stem).stem]['inherits']}.def.json")
            self._getDefs(parent_file)

    def _isDefinedInParent(self, key, value_dict, inherits_from):
        if "overrides" not in self._defs[inherits_from]:
            return self._isDefinedInParent(key, value_dict, self._defs[inherits_from]["inherits"])

        parent = self._defs[inherits_from]["overrides"]
        is_number = self._defs["fdmprinter"]["overrides"][key] in ("float", "int")
        for value in value_dict.values():
            if key in parent:
                check_values = [cv for cv in [parent[key].get("default_value", None), parent[key].get("value", None)] if cv is not None]
                for check_value in check_values:
                    if is_number:
                        try:
                            v = str(float(value))
                        except:
                            v = value
                        try:
                            cv = str(float(check_value))
                        except:
                            cv = check_value
                    else:
                        v = value
                        cv = check_value
                    if v == cv:
                        return True, value, parent

                if "inherits" in parent:
                    return self._isDefinedInParent(key, value_dict, parent["inherits"])
        return False, None, None
