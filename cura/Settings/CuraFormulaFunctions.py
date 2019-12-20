# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, List, Optional, TYPE_CHECKING

from UM.Settings.PropertyEvaluationContext import PropertyEvaluationContext
from UM.Settings.SettingFunction import SettingFunction
from UM.Logger import Logger

if TYPE_CHECKING:
    from cura.CuraApplication import CuraApplication
    from cura.Settings.CuraContainerStack import CuraContainerStack


#
# This class contains all Cura-related custom functions that can be used in formulas. Some functions requires
# information such as the currently active machine, so this is made into a class instead of standalone functions.
#
class CuraFormulaFunctions:

    def __init__(self, application: "CuraApplication") -> None:
        self._application = application

    # ================
    # Custom Functions
    # ================

    # Gets the default extruder position of the currently active machine.
    def getDefaultExtruderPosition(self) -> str:
        machine_manager = self._application.getMachineManager()
        return machine_manager.defaultExtruderPosition

    # Gets the given setting key from the given extruder position.
    def getValueInExtruder(self, extruder_position: int, property_key: str,
                           context: Optional["PropertyEvaluationContext"] = None) -> Any:
        machine_manager = self._application.getMachineManager()

        if extruder_position == -1:
            extruder_position = int(machine_manager.defaultExtruderPosition)

        global_stack = machine_manager.activeMachine
        try:
            extruder_stack = global_stack.extruderList[int(extruder_position)]
        except IndexError:
            if extruder_position != 0:
                Logger.log("w", "Value for %s of extruder %s was requested, but that extruder is not available. Returning the result from extruder 0 instead" % (property_key, extruder_position))
                # This fixes a very specific fringe case; If a profile was created for a custom printer and one of the
                # extruder settings has been set to non zero and the profile is loaded for a machine that has only a single extruder
                # it would cause all kinds of issues (and eventually a crash).
                # See https://github.com/Ultimaker/Cura/issues/5535
                return self.getValueInExtruder(0, property_key, context)
            Logger.log("w", "Value for %s of extruder %s was requested, but that extruder is not available. " % (property_key, extruder_position))
            return None

        value = extruder_stack.getRawProperty(property_key, "value", context = context)
        if isinstance(value, SettingFunction):
            value = value(extruder_stack, context = context)

        return value

    # Gets all extruder values as a list for the given property.
    def getValuesInAllExtruders(self, property_key: str,
                                context: Optional["PropertyEvaluationContext"] = None) -> List[Any]:
        machine_manager = self._application.getMachineManager()
        extruder_manager = self._application.getExtruderManager()

        global_stack = machine_manager.activeMachine

        result = []
        for extruder in extruder_manager.getActiveExtruderStacks():
            if not extruder.isEnabled:
                continue
            # only include values from extruders that are "active" for the current machine instance
            if int(extruder.getMetaDataEntry("position")) >= global_stack.getProperty("machine_extruder_count", "value", context = context):
                continue

            value = extruder.getRawProperty(property_key, "value", context = context)

            if value is None:
                continue

            if isinstance(value, SettingFunction):
                value = value(extruder, context = context)

            result.append(value)

        if not result:
            result.append(global_stack.getProperty(property_key, "value", context = context))

        return result

    # Get the resolve value or value for a given key.
    def getResolveOrValue(self, property_key: str, context: Optional["PropertyEvaluationContext"] = None) -> Any:
        machine_manager = self._application.getMachineManager()

        global_stack = machine_manager.activeMachine
        resolved_value = global_stack.getProperty(property_key, "value", context = context)

        return resolved_value

    # Gets the default setting value from given extruder position. The default value is what excludes the values in
    # the user_changes container.
    def getDefaultValueInExtruder(self, extruder_position: int, property_key: str) -> Any:
        machine_manager = self._application.getMachineManager()

        global_stack = machine_manager.activeMachine
        try:
            extruder_stack = global_stack.extruderList[extruder_position]
        except IndexError:
            Logger.log("w", "Unable to find extruder on in index %s", extruder_position)
        else:
            context = self.createContextForDefaultValueEvaluation(extruder_stack)

            return self.getValueInExtruder(extruder_position, property_key, context = context)

    # Gets all default setting values as a list from all extruders of the currently active machine.
    # The default values are those excluding the values in the user_changes container.
    def getDefaultValuesInAllExtruders(self, property_key: str) -> List[Any]:
        machine_manager = self._application.getMachineManager()

        global_stack = machine_manager.activeMachine

        context = self.createContextForDefaultValueEvaluation(global_stack)

        return self.getValuesInAllExtruders(property_key, context = context)

    # Gets the resolve value or value for a given key without looking the first container (user container).
    def getDefaultResolveOrValue(self, property_key: str) -> Any:
        machine_manager = self._application.getMachineManager()

        global_stack = machine_manager.activeMachine

        context = self.createContextForDefaultValueEvaluation(global_stack)
        return self.getResolveOrValue(property_key, context = context)

    # Creates a context for evaluating default values (skip the user_changes container).
    def createContextForDefaultValueEvaluation(self, source_stack: "CuraContainerStack") -> "PropertyEvaluationContext":
        context = PropertyEvaluationContext(source_stack)
        context.context["evaluate_from_container_index"] = 1  # skip the user settings container
        context.context["override_operators"] = {
            "extruderValue": self.getDefaultValueInExtruder,
            "extruderValues": self.getDefaultValuesInAllExtruders,
            "resolveOrValue": self.getDefaultResolveOrValue,
        }
        return context
