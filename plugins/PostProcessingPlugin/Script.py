# Copyright (c) 2015 Jaime van Kessel
# Copyright (c) 2018 Ultimaker B.V.
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.
from typing import Optional, Any, Dict, TYPE_CHECKING, List

from UM.Signal import Signal, signalemitter
from UM.i18n import i18nCatalog

# Setting stuff import
from UM.Application import Application
from UM.Settings.ContainerFormatError import ContainerFormatError
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry

import re
import json
import collections
i18n_catalog = i18nCatalog("cura")

if TYPE_CHECKING:
    from UM.Settings.Interfaces import DefinitionContainerInterface

# Some post-processing tasks are easy to parallelize. The easiest way to parallelize python code is via multiprocessing.
# Post-processing scripts aren't directly importable, though,  making them incompatible with multiprocessing.
# This module is importable, so it's possible to provide a workaround. The trick is to set up functions to call
# before multiprocessing forks the main process. That way, each forked process has a copy of the processing script.
# For example:
#         pool = multiprocessing.Pool(processes=multiprocessing.cpu_count(), initializer=multiprocessing_init,
#                                     initargs=({"process_layer": self.process_layer},))
#        result = pool.apply_async(multiprocessing_call, ("process_layer", (layer_steps,))))
#        return result.get()

## An inititializer for multiprocessing pools.
# \param functions_by_name A dict of callable functions called by name by multiprocessing_call(). The name is used
#                          to call the function.
def multiprocessing_init(functions_by_name):
    global _multiprocessing_functions
    _multiprocessing_functions = functions_by_name

## Calls the named function with the passed in arguments.
# \param function_name The function to call, as set up by multiprocessing_init().
# \param args The arguments to pass into the function when calling it.
# \return The return value of the function call.
def multiprocessing_call(function_name, args):
    return _multiprocessing_functions[function_name](*args)

## Base class for scripts. All scripts should inherit the script class.
@signalemitter
class Script:
    def __init__(self) -> None:
        super().__init__()
        self._stack = None  # type: Optional[ContainerStack]
        self._definition = None  # type: Optional[DefinitionContainerInterface]
        self._instance = None  # type: Optional[InstanceContainer]

    def initialize(self) -> None:
        setting_data = self.getSettingData()
        self._stack = ContainerStack(stack_id=str(id(self)))
        self._stack.setDirty(False)  # This stack does not need to be saved.

        ## Check if the definition of this script already exists. If not, add it to the registry.
        if "key" in setting_data:
            definitions = ContainerRegistry.getInstance().findDefinitionContainers(id=setting_data["key"])
            if definitions:
                # Definition was found
                self._definition = definitions[0]
            else:
                self._definition = DefinitionContainer(setting_data["key"])
                try:
                    self._definition.deserialize(json.dumps(setting_data))
                    ContainerRegistry.getInstance().addContainer(self._definition)
                except ContainerFormatError:
                    self._definition = None
                    return
        if self._definition is None:
            return
        self._stack.addContainer(self._definition)
        self._instance = InstanceContainer(container_id="ScriptInstanceContainer")
        self._instance.setDefinition(self._definition.getId())
        self._instance.setMetaDataEntry("setting_version",
                                        self._definition.getMetaDataEntry("setting_version", default=0))
        self._stack.addContainer(self._instance)
        self._stack.propertyChanged.connect(self._onPropertyChanged)

        ContainerRegistry.getInstance().addContainer(self._stack)

    settingsLoaded = Signal()
    valueChanged = Signal()  # Signal emitted whenever a value of a setting is changed

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if property_name == "value":
            self.valueChanged.emit()

            # Property changed: trigger reslice
            # To do this we use the global container stack propertyChanged.
            # Re-slicing is necessary for setting changes in this plugin, because the changes
            # are applied only once per "fresh" gcode
            global_container_stack = Application.getInstance().getGlobalContainerStack()
            if global_container_stack is not None:
                global_container_stack.propertyChanged.emit(key, property_name)

    ##  Needs to return a dict that can be used to construct a settingcategory file.
    #   See the example script for an example.
    #   It follows the same style / guides as the Uranium settings.
    #   Scripts can either override getSettingData directly, or use getSettingDataString
    #   to return a string that will be parsed as json. The latter has the benefit over
    #   returning a dict in that the order of settings is maintained.
    def getSettingData(self) -> Dict[str, Any]:
        setting_data_as_string = self.getSettingDataString()
        setting_data = json.loads(setting_data_as_string, object_pairs_hook = collections.OrderedDict)
        return setting_data

    def getSettingDataString(self) -> str:
        raise NotImplementedError()

    def getDefinitionId(self) -> Optional[str]:
        if self._stack:
            bottom = self._stack.getBottom()
            if bottom is not None:
                return bottom.getId()
        return None

    def getStackId(self) -> Optional[str]:
        if self._stack:
            return self._stack.getId()
        return None

    ##  Convenience function that retrieves value of a setting from the stack.
    def getSettingValueByKey(self, key: str) -> Any:
        if self._stack is not None:
            return self._stack.getProperty(key, "value")
        return None

    ##  Convenience function that finds the value in a line of g-code.
    #   When requesting key = x from line "G1 X100" the value 100 is returned.
    def getValue(self, line: str, key: str, default = None) -> Any:
        if not key in line or (';' in line and line.find(key) > line.find(';')):
            return default
        sub_part = line[line.find(key) + 1:]
        m = re.search('^-?[0-9]+\.?[0-9]*', sub_part)
        if m is None:
            return default
        try:
            return int(m.group(0))
        except ValueError: #Not an integer.
            try:
                return float(m.group(0))
            except ValueError: #Not a number at all.
                return default

    ##  Convenience function to produce a line of g-code.
    #
    #   You can put in an original g-code line and it'll re-use all the values
    #   in that line.
    #   All other keyword parameters are put in the result in g-code's format.
    #   For instance, if you put ``G=1`` in the parameters, it will output
    #   ``G1``. If you put ``G=1, X=100`` in the parameters, it will output
    #   ``G1 X100``. The parameters G and M will always be put first. The
    #   parameters T and S will be put second (or first if there is no G or M).
    #   The rest of the parameters will be put in arbitrary order.
    #   \param line The original g-code line that must be modified. If not
    #   provided, an entirely new g-code line will be produced.
    #   \return A line of g-code with the desired parameters filled in.
    def putValue(self, line: str = "", **kwargs) -> str:
        #Strip the comment.
        comment = ""
        if ";" in line:
            comment = line[line.find(";"):]
            line = line[:line.find(";")] #Strip the comment.

        #Parse the original g-code line.
        for part in line.split(" "):
            if part == "":
                continue
            parameter = part[0]
            if parameter in kwargs:
                continue #Skip this one. The user-provided parameter overwrites the one in the line.
            value = part[1:]
            kwargs[parameter] = value

        #Write the new g-code line.
        result = ""
        priority_parameters = ["G", "M", "T", "S", "F", "X", "Y", "Z", "E"] #First some parameters that get priority. In order of priority!
        for priority_key in priority_parameters:
            if priority_key in kwargs:
                if result != "":
                    result += " "
                result += priority_key + str(kwargs[priority_key])
                del kwargs[priority_key]
        for key, value in kwargs.items():
            if result != "":
                result += " "
            result += key + str(value)

        #Put the comment back in.
        if comment != "":
            if result != "":
                result += " "
            result += ";" + comment

        return result

    ##  This is called when the script is executed.
    #   It gets a list of g-code strings and needs to return a (modified) list.
    def execute(self, data: List[str]) -> List[str]:
        raise NotImplementedError()
