# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import configparser
import glob
import os
import re

from pathlib import Path
from typing import Any, Callable, cast, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry
from cura.CuraApplication import CuraApplication  # To find some resource types.
from cura.Settings.GlobalStack import GlobalStack
from cura.Settings.CuraContainerStack import _ContainerIndexes
from cura.Settings.CuraContainerRegistry import CuraContainerRegistry

from UM.PackageManager import PackageManager  # The class we're extending.
from UM.Resources import Resources  # To find storage paths for some resource types.
from UM.SaveFile import SaveFile  # To safely update the preferences file.
from UM.i18n import i18nCatalog
from urllib.parse import quote_plus, unquote_plus

catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from UM.Qt.QtApplication import QtApplication
    from PyQt6.QtCore import QObject


class CuraPackageManager(PackageManager):
    def __init__(self, application: "QtApplication", parent: Optional["QObject"] = None) -> None:
        super().__init__(application, parent)
        self._local_packages: Optional[List[Dict[str, Any]]] = None
        self._local_packages_ids: Optional[Set[str]] = None
        self.installedPackagesChanged.connect(self._updateLocalPackages)

    def _updateLocalPackages(self) -> None:
        self._local_packages = self.getAllLocalPackages()
        self._local_packages_ids = set(pkg["package_id"] for pkg in self._local_packages)

    @property
    def local_packages(self) -> List[Dict[str, Any]]:
        """locally installed packages, lazy execution"""
        if self._local_packages is None:
            self._updateLocalPackages()
            # _updateLocalPackages always results in a list of packages, not None.
            # It's guaranteed to be a list now.
        return cast(List[Dict[str, Any]], self._local_packages)

    @property
    def local_packages_ids(self) -> Set[str]:
        """locally installed packages, lazy execution"""
        if self._local_packages_ids is None:
            self._updateLocalPackages()
            # _updateLocalPackages always results in a list of packages, not None.
            # It's guaranteed to be a list now.
        return cast(Set[str], self._local_packages_ids)

    def initialize(self) -> None:
        self._installation_dirs_dict["materials"] = Resources.getStoragePath(CuraApplication.ResourceTypes.MaterialInstanceContainer)
        self._installation_dirs_dict["qualities"] = Resources.getStoragePath(CuraApplication.ResourceTypes.QualityInstanceContainer)
        self._installation_dirs_dict["variants"] = Resources.getStoragePath(
            CuraApplication.ResourceTypes.VariantInstanceContainer)
        self._installation_dirs_dict["images"] = Resources.getStoragePath(CuraApplication.ResourceTypes.ImageFiles)

        # Due to a bug in Cura 5.1.0 we needed to change the directory structure of the curapackage on the server side (See SD-3871).
        # Although the material intent profiles will be installed in the `intent` folder, the curapackage from the server side will
        # have an `intents` folder. For completeness, we will look in both locations of in the curapackage and map them both to the
        # `intent` folder.
        self._installation_dirs_dict["intents"] = Resources.getStoragePath(CuraApplication.ResourceTypes.IntentInstanceContainer)
        self._installation_dirs_dict["intent"] = Resources.getStoragePath(CuraApplication.ResourceTypes.IntentInstanceContainer)

        super().initialize()

    def _preparePackageRemoval(self, package_id: str) -> Optional[Callable[[], None]]:
        definition_ids = self._getPackageDefinitionIds(package_id)
        if not definition_ids:
            return None
        return lambda: self._cleanUpUninstalledPackage(package_id, definition_ids)

    def _cleanUpUninstalledPackage(self, package_id: str, definition_ids: Optional[Set[str]] = None) -> None:
        """Remove the printers that use the definitions of a package that is being uninstalled.

        The machine stacks, extruder stacks and the user, definition changes and quality changes containers of those
        printers are stored in the configuration folder. If they stay behind, they refer to definitions that no longer
        exist, which corrupts the configuration. This happens before the containers are loaded, so the files are
        handled directly. Definition IDs are captured before the package files are removed.

        :param package_id: The ID of the package that is being uninstalled.
        """
        self._replaceMissingContainers(package_id)

        if definition_ids is None:
            definition_ids = self._getPackageDefinitionIds(package_id)
        if not definition_ids:
            return

        # A definition that is also available from elsewhere, such as the version that ships with the application, is
        # still there after the package is removed. The printers that use it are kept: they continue with that version.
        kept_definition_ids = definition_ids & self._getAvailableDefinitionIds(package_id)
        if kept_definition_ids:
            Logger.info(f"The definitions {sorted(kept_definition_ids)} of package [{package_id}] are also available without it, so the printers that use them are kept.")
        definition_ids = definition_ids - kept_definition_ids
        if not definition_ids:
            return

        resource_types = CuraApplication.ResourceTypes
        machine_stacks = [(path, parser) for path, parser in self._readConfigFiles(Resources.getStoragePath(resource_types.MachineStack), ".global.cfg")
                          if parser.has_option("general", "id")]
        extruder_stacks = [(path, parser) for path, parser in self._readConfigFiles(Resources.getStoragePath(resource_types.ExtruderStack), ".extruder.cfg")
                           if parser.has_option("general", "id")]

        # A printer is removed if its own definition or the definition of one of its extruders is from the package.
        machine_ids = {parser["general"]["id"] for _, parser in machine_stacks if self._usesDefinition(parser, definition_ids)}
        for _, parser in extruder_stacks:
            if self._usesDefinition(parser, definition_ids) and parser.has_option("metadata", "machine"):
                machine_ids.add(parser["metadata"]["machine"])

        stacks_to_remove = [(path, parser) for path, parser in machine_stacks if parser["general"]["id"] in machine_ids]
        stacks_to_remove += [(path, parser) for path, parser in extruder_stacks
                             if self._usesDefinition(parser, definition_ids)
                             or parser.get("metadata", "machine", fallback = None) in machine_ids]

        paths_to_remove = [path for path, _ in stacks_to_remove]

        # The user changes and the definition changes are only used by the stack they were created for.
        for resource_type in (resource_types.UserInstanceContainer, resource_types.DefinitionChangesContainer):
            container_dir = Resources.getStoragePath(resource_type)
            for _, stack in stacks_to_remove:
                if stack.has_section("containers"):
                    for container_id in stack["containers"].values():
                        path = os.path.join(container_dir, quote_plus(container_id) + ".inst.cfg")
                        if os.path.isfile(path):
                            paths_to_remove.append(path)

        # Containers of those types for the definitions of the package, whether or not a stack still refers to them.
        # Quality changes are shared by all printers with the same definition, so they are only found this way.
        for resource_type in (resource_types.UserInstanceContainer, resource_types.DefinitionChangesContainer,
                              resource_types.QualityChangesInstanceContainer):
            for path, parser in self._readConfigFiles(Resources.getStoragePath(resource_type), ".inst.cfg"):
                if parser.get("general", "definition", fallback = None) in definition_ids:
                    paths_to_remove.append(path)

        for path in dict.fromkeys(paths_to_remove):  # Without duplicates, in order.
            Logger.info(f"Removing '{path}' because package [{package_id}] is uninstalled.")
            try:
                os.remove(path)
            except OSError as e:
                Logger.warning(f"Unable to remove '{path}' for the uninstalled package [{package_id}]: {e}")

        # The printer that was active may be gone now, so make another one the active printer.
        remaining_machine_ids = [parser["general"]["id"] for _, parser in sorted(machine_stacks, key = lambda stack: stack[0])
                                 if parser["general"]["id"] not in machine_ids]
        self._replaceActiveMachine(machine_ids, remaining_machine_ids)

    def _replaceActiveMachine(self, removed_machine_ids: Set[str], remaining_machine_ids: List[str]) -> None:
        """If the active printer was removed, make another printer the active printer.

        The active printer is stored in the preferences file, which is read after the packages are uninstalled. If no
        other printer is available, nothing is changed.

        :param removed_machine_ids: The IDs of the printers that were removed.
        :param remaining_machine_ids: The IDs of the printers that are still available, in order of preference.
        """
        if not removed_machine_ids or not remaining_machine_ids:
            return

        preferences_path = Resources.getStoragePath(Resources.Preferences, f"{self._application.getApplicationName()}.cfg")
        preferences = configparser.ConfigParser(interpolation = None)
        try:
            if not preferences.read(preferences_path, encoding = "utf-8"):
                return  # No preferences file yet, so there is no active printer.
        except (configparser.Error, OSError, UnicodeDecodeError):
            Logger.warning(f"Unable to read '{preferences_path}' to check if the active printer was removed.")
            return

        active_machine_id = preferences.get("cura", "active_machine", fallback = "")
        if active_machine_id not in removed_machine_ids:
            return

        new_active_machine_id = remaining_machine_ids[0]
        Logger.info(f"The active printer [{active_machine_id}] was removed, so [{new_active_machine_id}] is now the active printer.")
        preferences["cura"]["active_machine"] = new_active_machine_id
        try:
            with SaveFile(preferences_path, "wt") as f:
                preferences.write(f)
        except OSError as e:
            Logger.warning(f"Unable to set the active printer in '{preferences_path}': {e}")

    def _getPackageDefinitionIds(self, package_id: str) -> Set[str]:
        """Get the IDs of the machine and extruder definitions that an installed package provides.

        The definitions are looked for in the folders of the package in the configuration folder, as before, and in the
        "definitions" and "extruders" folders of the plugin of the package, which is used in place.
        """
        suffix = ".def.json"
        resource_types = CuraApplication.ResourceTypes
        definition_dirs = [os.path.join(Resources.getStoragePath(Resources.DefinitionContainers), package_id),
                           os.path.join(Resources.getStoragePath(resource_types.ExtruderStack), package_id)]

        plugin_dir = os.path.join(self._installation_dirs_dict["plugins"], package_id)
        for root, dir_names, _ in os.walk(plugin_dir):
            if os.path.basename(root) in ("definitions", "extruders"):
                definition_dirs.append(root)
                dir_names.clear()  # Everything below is already covered by this folder.

        definition_ids = set()
        for definition_dir in definition_dirs:
            for _, _, file_names in os.walk(definition_dir):
                for file_name in file_names:
                    if file_name.endswith(suffix):
                        definition_ids.add(unquote_plus(file_name[:-len(suffix)]))
        return definition_ids

    def _getAvailableDefinitionIds(self, package_id: str) -> Set[str]:
        """Get the IDs of the machine and extruder definitions that are available without a package.

        These are the definitions in the resource folders, such as the ones that ship with the application, and the
        definitions of the other installed packages that stay installed.

        :param package_id: The ID of the package to leave out.
        """
        resource_types = CuraApplication.ResourceTypes
        return self._getAvailableIds(package_id, [Resources.DefinitionContainers, resource_types.ExtruderStack], ["definitions", "extruders"], ".def.json")

    def _getAvailableIds(self, package_id: str, resource_type_list: List[int], plugin_folders: List[str], suffix: str) -> Set[str]:
        """Get the IDs of the containers of some types that are available without a package.

        :param package_id: The ID of the package to leave out.
        :param resource_type_list: The resource types of the folders to look in.
        :param plugin_folders: The names of the folders in the other installed packages to look in.
        :param suffix: The end of the names of the files of the containers.
        """
        package_dirs = [os.path.join(Resources.getStoragePath(resource_type), package_id) for resource_type in resource_type_list]
        package_dirs.append(os.path.join(self._installation_dirs_dict["plugins"], package_id))

        container_dirs = []  # type: List[str]
        for resource_type in resource_type_list:
            container_dirs += Resources.getAllPathsForType(resource_type)
        plugins_dir = self._installation_dirs_dict["plugins"]
        try:
            other_package_ids = os.listdir(plugins_dir)
        except OSError:
            other_package_ids = []
        for other_package_id in other_package_ids:
            if other_package_id != package_id and other_package_id not in self._to_remove_package_set:
                container_dirs += [os.path.join(plugins_dir, other_package_id, folder) for folder in plugin_folders]

        container_ids = set()  # type: Set[str]
        for container_dir in container_dirs:
            if any(self._isInside(container_dir, package_dir) for package_dir in package_dirs):
                continue
            for root, dir_names, file_names in os.walk(container_dir):
                # The folder of the package can be inside of one of the resource folders.
                dir_names[:] = [name for name in dir_names if not any(self._isInside(os.path.join(root, name), package_dir) for package_dir in package_dirs)]
                for file_name in file_names:
                    if file_name.endswith(suffix):
                        container_ids.add(unquote_plus(file_name[:-len(suffix)]))
        return container_ids

    def _getPackageIds(self, package_id: str, resource_type_list: List[int], plugin_folders: List[str], suffix: str) -> Set[str]:
        """Get the IDs of the containers of some types that an installed package provides, in the folders of the
        package in the configuration folder and in the folders of the plugin of the package."""

        container_dirs = [os.path.join(Resources.getStoragePath(resource_type), package_id) for resource_type in resource_type_list]
        plugin_dir = os.path.join(self._installation_dirs_dict["plugins"], package_id)
        container_dirs += [os.path.join(plugin_dir, folder) for folder in plugin_folders]

        container_ids = set()  # type: Set[str]
        for container_dir in container_dirs:
            for _, _, file_names in os.walk(container_dir):
                for file_name in file_names:
                    if file_name.endswith(suffix):
                        container_ids.add(unquote_plus(file_name[:-len(suffix)]))
        return container_ids

    def _replaceMissingContainers(self, package_id: str) -> None:
        """Replace the variants, quality profiles and intents of a package that is uninstalled by empty containers.

        The printers that remain can still use these, for instance a nozzle that is only in the package. A container
        stack that refers to a container that doesn't exist is considered corrupt and is not loaded. With an empty
        container in its place, the printer is loaded and Cura selects another variant or profile by itself.

        This happens before the containers are loaded, so the files of the stacks are handled directly.
        """
        resource_types = CuraApplication.ResourceTypes
        # The position of the container in the stack, the resource type and the name of the folder in a plugin.
        kinds = {
            _ContainerIndexes.Intent: (resource_types.IntentInstanceContainer, "intent", "empty_intent"),
            _ContainerIndexes.Quality: (resource_types.QualityInstanceContainer, "quality", "empty_quality"),
            _ContainerIndexes.Variant: (resource_types.VariantInstanceContainer, "variants", "empty_variant"),
        }
        replacements = {}  # type: Dict[str, Tuple[Set[str], str]]  # Position -> the container IDs that disappear and what replaces them.
        for index, (resource_type, plugin_folder, empty_id) in kinds.items():
            disappearing = self._getPackageIds(package_id, [resource_type], [plugin_folder], ".inst.cfg") - \
                self._getAvailableIds(package_id, [resource_type], [plugin_folder], ".inst.cfg")
            if disappearing:
                replacements[str(index)] = (disappearing, empty_id)
        if not replacements:
            return

        for stack_type, suffix in ((resource_types.MachineStack, ".global.cfg"), (resource_types.ExtruderStack, ".extruder.cfg")):
            stack_dir = Resources.getStoragePath(stack_type)
            try:
                file_names = [name for name in os.listdir(stack_dir) if name.endswith(suffix)]
            except OSError:
                continue
            for file_name in file_names:
                path = os.path.join(stack_dir, file_name)
                try:
                    with open(path, "rb") as f:
                        lines = f.read().decode("utf-8").splitlines(keepends = True)
                except (OSError, UnicodeDecodeError):
                    Logger.warning(f"Unable to read '{path}' to check if it refers to containers of uninstalled package [{package_id}].")
                    continue

                changed = False
                in_containers = False
                for line_number, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("["):
                        in_containers = stripped == "[containers]"
                        continue
                    match = re.match(r"^(\d+)(\s*=\s*)(.*?)(\r?\n?)$", line) if in_containers else None
                    if match and match.group(1) in replacements and match.group(3) in replacements[match.group(1)][0]:
                        Logger.info(f"'{path}' refers to container [{match.group(3)}] of uninstalled package [{package_id}], replacing it by an empty container.")
                        lines[line_number] = match.group(1) + match.group(2) + replacements[match.group(1)][1] + match.group(4)
                        changed = True
                if changed:
                    try:
                        with open(path, "wb") as f:
                            f.write("".join(lines).encode("utf-8"))
                    except OSError as e:
                        Logger.warning(f"Unable to update '{path}' for the uninstalled package [{package_id}]: {e}")

    @staticmethod
    def _isInside(path: str, folder: str) -> bool:
        """Whether a path is the folder or inside of it."""
        path, folder = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(folder))
        return path == folder or path.startswith(folder + os.sep)

    @staticmethod
    def _usesDefinition(stack: configparser.ConfigParser, definition_ids: Set[str]) -> bool:
        """Whether a serialized container stack contains one of the given definitions."""
        # The position of the definition differs between versions of the file, so look at all of the containers.
        return stack.has_section("containers") and any(container_id in definition_ids for container_id in stack["containers"].values())

    @staticmethod
    def _readConfigFiles(directory: str, suffix: str) -> List[Tuple[str, configparser.ConfigParser]]:
        """Read the configuration files with the given suffix in a folder (without sub-folders).

        Files that can't be read are skipped.
        """
        try:
            file_names = os.listdir(directory)
        except OSError:
            return []

        result = []
        for file_name in file_names:
            path = os.path.join(directory, file_name)
            if not file_name.endswith(suffix) or not os.path.isfile(path):
                continue
            parser = configparser.ConfigParser(interpolation = None, empty_lines_in_values = False)
            try:
                parser.read(path, encoding = "utf-8")
            except (configparser.Error, OSError, UnicodeDecodeError):
                Logger.warning(f"Unable to read '{path}' to check if it depends on an uninstalled package.")
                continue
            result.append((path, parser))
        return result

    def isMaterialBundled(self, file_name: str, guid: str):
        """ Check if there is a bundled material name with file_name and guid """
        for path in Resources.getSecureSearchPaths():
            # Secure search paths are install directory paths, if a material is in here it must be bundled.

            paths = [Path(p) for p in glob.glob(path + '/**/*.xml.fdm_material', recursive=True)]
            for material in paths:
                if material.name == file_name:
                    Logger.info(f"Found bundled material: {material.name}. Located in path: {str(material)}")
                    with open(material, encoding="utf-8") as f:
                        # Make sure the file we found has the same guid as our material
                        # Parsing this xml would be better but the namespace is needed to search it.
                        parsed_guid = PluginRegistry.getInstance().getPluginObject(
                            "XmlMaterialProfile").getMetadataFromSerialized(
                            f.read(), "GUID")
                        if guid == parsed_guid:
                            # The material we found matches both filename and GUID
                            return True

        return False

    def getMaterialFilePackageId(self, file_name: str, guid: str) -> str:
        """Get the id of the installed material package that contains file_name"""
        file_name = unquote_plus(file_name)
        for material_package in [f for f in os.scandir(self._installation_dirs_dict["materials"]) if f.is_dir()]:
            package_id = material_package.name

            for root, _, file_names in os.walk(material_package.path):
                if file_name not in file_names:
                    # File with the name we are looking for is not in this directory
                    continue

                with open(os.path.join(root, file_name), encoding="utf-8") as f:
                    # Make sure the file we found has the same guid as our material
                    # Parsing this xml would be better but the namespace is needed to search it.
                    parsed_guid = PluginRegistry.getInstance().getPluginObject("XmlMaterialProfile").getMetadataFromSerialized(
                        f.read(), "GUID")

                    if guid == parsed_guid:
                        return package_id

        Logger.error("Could not find package_id for file: {} with GUID: {} ".format(file_name, guid))
        Logger.error(f"Bundled paths searched: {list(Resources.getSecureSearchPaths())}")
        return ""

    def getMachinesUsingPackage(self, package_id: str) -> Tuple[List[Tuple[GlobalStack, str, str]], List[Tuple[GlobalStack, str, str]]]:
        """Returns a list of where the package is used

        It loops through all the package contents and see if some of the ids are used.

        :param package_id: package id to search for
        :return: empty if it is never used, otherwise a list consisting of 3-tuples
        """

        ids = self.getPackageContainerIds(package_id)
        global_stacks = CuraContainerRegistry.getInstance().findGlobalStacks()
        machine_with_materials = []
        machine_with_qualities = []
        for container_id in ids:
            for global_stack in global_stacks:
                for extruder_nr, extruder_stack in enumerate(global_stack.extruderList):
                    if container_id in (extruder_stack.material.getId(), extruder_stack.material.getMetaData().get("base_file")):
                        machine_with_materials.append((global_stack, str(extruder_nr), container_id))
                    if container_id == extruder_stack.quality.getId():
                        machine_with_qualities.append((global_stack, str(extruder_nr), container_id))

        return machine_with_materials, machine_with_qualities

    def getAllLocalPackages(self) -> List[Dict[str, Any]]:
        """ Returns an unordered list of all the package_info of installed, to be installed, or bundled packages"""
        packages: List[Dict[str, Any]] = []

        for packages_to_add in self.getAllInstalledPackagesInfo().values():
            packages.extend(packages_to_add)

        return packages
