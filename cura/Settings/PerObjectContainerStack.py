# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Optional

from UM.Application import Application
from UM.Decorators import override
from UM.Settings.Interfaces import PropertyEvaluationContext
from UM.Settings.SettingInstance import InstanceState

from .CuraContainerStack import CuraContainerStack


class PerObjectContainerStack(CuraContainerStack):
    @override(CuraContainerStack)
    def getProperty(self, key: str, property_name: str, context: Optional[PropertyEvaluationContext] = None) -> Any:
        if context is None:
            context = PropertyEvaluationContext()
        context.pushContainer(self)

        global_stack = Application.getInstance().getGlobalContainerStack()
        if not global_stack:
            return None

        # Return the user defined value if present, otherwise, evaluate the value according to the default routine.
        if self.getContainer(0).hasProperty(key, property_name):
            if self.getContainer(0).getProperty(key, "state") == InstanceState.User:
                result = super().getProperty(key, property_name, context)
                context.popContainer()
                return result

        # Handle the "limit_to_extruder" property.
        limit_to_extruder = super().getProperty(key, "limit_to_extruder", context)
        if limit_to_extruder is not None:
            limit_to_extruder = str(limit_to_extruder)

        # if this stack has the limit_to_extruder "not overridden", use the original limit_to_extruder as the current
        # limit_to_extruder, so the values retrieved will be from the perspective of the original limit_to_extruder
        # stack.
        if limit_to_extruder == "-1":
            if "original_limit_to_extruder" in context.context:
                limit_to_extruder = context.context["original_limit_to_extruder"]

        if limit_to_extruder is not None and limit_to_extruder != "-1" and limit_to_extruder in global_stack.extruders:
            # set the original limit_to_extruder if this is the first stack that has a non-overridden limit_to_extruder
            if "original_limit_to_extruder" not in context.context:
                context.context["original_limit_to_extruder"] = limit_to_extruder

            if super().getProperty(key, "settable_per_extruder", context):
                result = global_stack.extruders[str(limit_to_extruder)].getProperty(key, property_name, context)
                if result is not None:
                    context.popContainer()
                    return result

        result = super().getProperty(key, property_name, context)
        context.popContainer()
        return result

    @override(CuraContainerStack)
    def setNextStack(self, stack: CuraContainerStack) -> None:
        super().setNextStack(stack)

        # trigger signal to re-evaluate all default settings
        for key in self.getContainer(0).getAllKeys():
            # only evaluate default settings
            if self.getContainer(0).getProperty(key, "state") != InstanceState.Default:
                continue

            self._collectPropertyChanges(key, "value")
        self._emitCollectedPropertyChanges()
