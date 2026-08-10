import json
import re
from configparser import ConfigParser
from pathlib import Path
from typing import ClassVar, Dict, Iterator, List, Optional, Set

from ..diagnostic import Diagnostic
from .linter import Linter


class CircularDependency(Linter):
    """Detects circular setting value dependencies in definition and profile files.

    A circular dependency occurs when two or more settings reference each other,
    directly or indirectly, through their ``value`` formulas. For example:

    - ``ultimaker.def.json`` sets ``bridge_wall_speed = "bridge_skin_speed"``
    - A quality profile overrides ``bridge_skin_speed = =bridge_wall_speed``

    Combined, this creates the cycle ``bridge_wall_speed -> bridge_skin_speed ->
    bridge_wall_speed``, which will cause infinite recursion at runtime.
    """

    _setting_names_cache: ClassVar[Optional[Set[str]]] = None

    def __init__(self, file: Path, settings: dict) -> None:
        super().__init__(file, settings)
        self._all_setting_names: Set[str] = set()
        self._load_all_setting_names()

    def check(self) -> Iterator[Diagnostic]:
        if self._settings["checks"].get("diagnostic-circular-dependency", False):
            for check in self.checkCircularDependencies():
                yield check
        yield

    def checkCircularDependencies(self) -> Iterator[Diagnostic]:
        if self._file.suffix == ".cfg":
            yield from self._check_profile()
        elif self._file.suffix == ".json":
            yield from self._check_definition()

    def _check_profile(self) -> Iterator[Diagnostic]:
        """Check a .inst.cfg quality/material/variant profile for circular dependencies.

        Profile constant overrides (e.g. ``bridge_wall_speed = 30``) are intentionally
        **excluded** from the dependency graph.  Cura exposes a "reset to formula"
        button for every setting, so a constant can always be reverted to the
        ancestor definition's ``value`` formula.  Only formula-based overrides
        (values that start with ``=``) are applied on top of the definition chain.
        """
        config = ConfigParser()
        config.read([self._file])

        if not config.has_option("general", "definition"):
            return

        def_name = config.get("general", "definition")
        defs_dir = self._find_definitions_dir()
        if defs_dir is None:
            return

        def_file = defs_dir / f"{def_name}.def.json"
        # Start from the *definition chain* graph — constant overrides in the
        # profile do NOT remove these edges.
        def_value_map = self._build_value_map_from_def_hierarchy(def_file)
        graph = self._build_graph(def_value_map)

        # Overlay only the profile's *formula* overrides (``= …`` values).
        # These genuinely change which setting a key depends on.
        profile_formula_keys: Set[str] = set()
        if config.has_section("values"):
            for key in config.options("values"):
                val = config.get("values", key)
                if val.startswith("="):
                    refs = self._extract_references(val)
                    if refs:
                        graph[key] = refs
                    elif key in graph:
                        del graph[key]
                    profile_formula_keys.add(key)

        cycle = self._detect_cycle(graph)

        # Only report when at least one formula-override in this profile is part
        # of the cycle; otherwise the cycle already existed in the definition.
        if cycle and any(node in profile_formula_keys for node in cycle):
            content = self._file.read_text()
            offset = self._find_offset_for_cycle_node(content, cycle, profile_formula_keys)
            yield Diagnostic(
                file=self._file,
                diagnostic_name="diagnostic-circular-dependency",
                message=(
                    f"Circular dependency detected across settings: {' -> '.join(cycle)}. "
                    f"This profile sets a formula override that forms a cycle with the "
                    f"inherited definition value. Even if a constant override currently "
                    f"hides the cycle, resetting any setting in the cycle to its formula "
                    f"will cause infinite recursion."
                ),
                level="Error",
                offset=offset,
            )

    def _check_definition(self) -> Iterator[Diagnostic]:
        """Check a .def.json definition file for circular dependencies."""
        if not self._file.exists():
            return

        def_name = Path(self._file.stem).stem
        if def_name in ("fdmprinter", "fdmextruder"):
            return

        data = json.loads(self._file.read_text())
        this_def_keys: Set[str] = set(data.get("overrides", {}).keys())

        value_map = self._build_value_map_from_def_hierarchy(self._file)
        graph = self._build_graph(value_map)
        cycle = self._detect_cycle(graph)

        # Only report when at least one node in the cycle is overridden by this
        # specific definition file.
        if cycle and any(node in this_def_keys for node in cycle):
            content = self._file.read_text()
            offset = self._find_offset_for_cycle_node(content, cycle, this_def_keys)
            yield Diagnostic(
                file=self._file,
                diagnostic_name="diagnostic-circular-dependency",
                message=(
                    f"Circular dependency detected across settings: {' -> '.join(cycle)}. "
                    f"Check the 'value' formulas for these settings in this file and its "
                    f"parent definitions."
                ),
                level="Error",
                offset=offset,
            )

    def _build_graph(self, value_map: Dict[str, str]) -> Dict[str, Set[str]]:
        """Build a directed dependency graph from a setting-name -> formula map."""
        graph: Dict[str, Set[str]] = {}
        for key, formula in value_map.items():
            refs = self._extract_references(formula)
            if refs:
                graph[key] = refs
        return graph

    def _detect_cycle(self, graph: Dict[str, Set[str]]) -> Optional[List[str]]:
        """Depth-First-Search-based cycle detection.

        Returns the cycle as a list of node names where the first and last element
        are the same (e.g. ``['a', 'b', 'a']``), or ``None`` if no cycle exists.
        Iteration order is sorted for deterministic output.
        """
        visited: Set[str] = set()

        def depth_first_search(node: str, path: List[str], path_set: Set[str]) -> Optional[List[str]]:
            visited.add(node)
            path.append(node)
            path_set.add(node)
            for neighbor in sorted(graph.get(node, set())):
                if neighbor in path_set:
                    start = path.index(neighbor)
                    return path[start:] + [neighbor]
                if neighbor not in visited:
                    result = depth_first_search(neighbor, path, path_set)
                    if result is not None:
                        return result
            path.pop()
            path_set.discard(node)
            return None

        for node in sorted(graph.keys()):
            if node not in visited:
                result = depth_first_search(node, [], set())
                if result is not None:
                    return result
        return None

    def _extract_references(self, formula) -> Set[str]:
        """Return the set of known setting names referenced by *formula*.

        Handles both the JSON format (plain string, e.g. ``"bridge_skin_speed"``)
        and the .cfg profile format (leading ``=``, e.g. ``=bridge_skin_speed``).
        Complex expressions like ``math.ceil(speed_wall * 30 / 35)`` are tokenised
        and each word token is checked against the known setting name list.
        """
        if not isinstance(formula, str):
            return set()
        if formula.startswith("="):
            formula = formula[1:]
        tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula)
        return {t for t in tokens if t in self._all_setting_names}

    def _build_value_map_from_def_hierarchy(self, def_file: Path) -> Dict[str, str]:
        """Recursively collect ``value`` formulas from a definition's full chain.

        Parent values are loaded first; child overrides win. Both the top-level
        ``settings`` key (used in *fdmprinter* / *fdmextruder*) and the ``overrides``
        key (used in all other definitions) are processed.
        """
        if not def_file.exists():
            return {}

        data = json.loads(def_file.read_text())
        value_map: Dict[str, str] = {}

        if "inherits" in data:
            parent_name = data["inherits"]
            parent_file = def_file.parent / f"{parent_name}.def.json"
            if not parent_file.exists():
                defs_dir = self._find_definitions_dir()
                if defs_dir:
                    parent_file = defs_dir / f"{parent_name}.def.json"
            value_map = self._build_value_map_from_def_hierarchy(parent_file)

        # Base printer definitions store settings in a nested "settings" tree.
        if "settings" in data:
            self._extract_values_from_settings_tree(data["settings"], value_map)

        # All other definitions use a flat "overrides" dict.
        for key, value_dict in data.get("overrides", {}).items():
            if isinstance(value_dict, dict) and "value" in value_dict:
                value_map[key] = str(value_dict["value"])

        return value_map

    def _extract_values_from_settings_tree(self, settings_obj: dict, result: Dict[str, str]) -> None:
        """Recursively walk a ``settings`` tree and collect ``value`` entries."""
        for key, value in settings_obj.items():
            if isinstance(value, dict):
                if "value" in value:
                    result[key] = str(value["value"])
                if "children" in value:
                    self._extract_values_from_settings_tree(value["children"], result)

    def _find_definitions_dir(self) -> Optional[Path]:
        """Walk up the directory tree to locate ``resources/definitions``."""
        for search in (self._file.parent, *self._file.parent.parents):
            candidate = search / "resources" / "definitions"
            if candidate.exists():
                return candidate
        return None

    def _load_all_setting_names(self) -> None:
        """Populate ``_all_setting_names`` from the two base definition files.

        The result is cached at class level so the two base JSON files are only
        read and parsed once, regardless of how many ``CircularDependency``
        instances are created during a linting run.
        """
        if CircularDependency._setting_names_cache is not None:
            self._all_setting_names = CircularDependency._setting_names_cache
            return
        defs_dir = self._find_definitions_dir()
        if defs_dir is None:
            return
        for base_name in ("fdmprinter.def.json", "fdmextruder.def.json"):
            f = defs_dir / base_name
            if f.exists():
                data = json.loads(f.read_text())
                self._collect_setting_keys(data.get("settings", {}))
        CircularDependency._setting_names_cache = self._all_setting_names

    def _collect_setting_keys(self, settings_obj: dict) -> None:
        """Recursively collect all setting keys from a settings tree."""
        for key, value in settings_obj.items():
            if isinstance(value, dict):
                if "label" in value:
                    self._all_setting_names.add(key)
                if "children" in value:
                    self._collect_setting_keys(value["children"])

    def _find_offset_for_cycle_node(
        self, content: str, cycle: List[str], preferred_keys: Set[str]
    ) -> int:
        """Return the byte offset of the first cycle node that belongs to *preferred_keys*."""
        for node in cycle:
            if node in preferred_keys:
                # For JSON files the key appears as "node_name"
                for pattern in (f'"{node}"', node):
                    idx = content.find(pattern)
                    if idx >= 0:
                        return idx
        return 0
