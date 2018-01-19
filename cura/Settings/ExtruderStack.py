# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, TYPE_CHECKING, Optional

from UM.Decorators import override
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface, PropertyEvaluationContext
from UM.Settings.SettingInstance import SettingInstance

from . import Exceptions
from .CuraContainerStack import CuraContainerStack
from .ExtruderManager import ExtruderManager

if TYPE_CHECKING:
    from cura.Settings.GlobalStack import GlobalStack


##  Represents an Extruder and its related containers.
#
#
class ExtruderStack(CuraContainerStack):
    def __init__(self, container_id: str, *args, **kwargs):
        super().__init__(container_id, *args, **kwargs)

        self.addMetaDataEntry("type", "extruder_train") # For backward compatibility

        self.propertiesChanged.connect(self._onPropertiesChanged)

    ##  Overridden from ContainerStack
    #
    #   This will set the next stack and ensure that we register this stack as an extruder.
    @override(ContainerStack)
    def setNextStack(self, stack: ContainerStack) -> None:
        super().setNextStack(stack)
        stack.addExtruder(self)
        self.addMetaDataEntry("machine", stack.id)

        # For backward compatibility: Register the extruder with the Extruder Manager
        ExtruderManager.getInstance().registerExtruder(self, stack.id)

        # Now each machine will have at least one extruder stack. If this is the first extruder, the extruder-specific
        # settings such as nozzle size and material diameter should be moved from the machine's definition_changes to
        # the this extruder's definition_changes.
        #
        # We do this here because it is tooooo expansive to do it in the version upgrade: During the version upgrade,
        # when we are upgrading a definition_changes container file, there is NO guarantee that other files such as
        # machine an extruder stack files are upgraded before this, so we cannot read those files assuming they are in
        # the latest format.
        #
        # MORE:
        # For single-extrusion machines, nozzle size is saved in the global stack, so the nozzle size value should be
        # carried to the first extruder.
        # For material diameter, it was supposed to be applied to all extruders, so its value should be copied to all
        # extruders.
        #
        keys_to_copy = ["material_diameter"]  # material diameter will be copied to all extruders
        if self.getMetaDataEntry("position") == "0":
            keys_to_copy.append("machine_nozzle_size")

        for key in keys_to_copy:
            # Only copy the value when this extruder doesn't have the value.
            if self.definitionChanges.hasProperty(key, "value"):
                continue
            setting_value = stack.definitionChanges.getProperty(key, "value")
            if setting_value is None:
                continue

            setting_definition = stack.getSettingDefinition(key)
            new_instance = SettingInstance(setting_definition, self.definitionChanges)
            new_instance.setProperty("value", setting_value)
            new_instance.resetState()  # Ensure that the state is not seen as a user state.
            self.definitionChanges.addInstance(new_instance)
            self.definitionChanges.setDirty(True)

            # NOTE: We cannot remove the setting from the global stack's definition changes container because for
            # material diameter, it needs to be applied to all extruders, but here we don't know how many extruders
            # a machine actually has and how many extruders has already been loaded for that machine, so we have to
            # keep this setting for any remaining extruders that haven't been loaded yet.
            #
            # Those settings will be removed in ExtruderManager which knows all those info.

    @override(ContainerStack)
    def getNextStack(self) -> Optional["GlobalStack"]:
        return super().getNextStack()

    @classmethod
    def getLoadingPriority(cls) -> int:
        return 3

    ##  Overridden from ContainerStack
    #
    #   It will perform a few extra checks when trying to get properties.
    #
    #   The two extra checks it currently does is to ensure a next stack is set and to bypass
    #   the extruder when the property is not settable per extruder.
    #
    #   \throws Exceptions.NoGlobalStackError Raised when trying to get a property from an extruder without
    #                                         having a next stack set.
    @override(ContainerStack)
    def getProperty(self, key: str, property_name: str, context: Optional[PropertyEvaluationContext] = None) -> Any:
        if not self._next_stack:
            raise Exceptions.NoGlobalStackError("Extruder {id} is missing the next stack!".format(id = self.id))

        if context is None:
            context = PropertyEvaluationContext()
        context.pushContainer(self)

        if not super().getProperty(key, "settable_per_extruder", context):
            result = self.getNextStack().getProperty(key, property_name, context)
            context.popContainer()
            return result

        limit_to_extruder = super().getProperty(key, "limit_to_extruder", context)
        if limit_to_extruder is not None:
            limit_to_extruder = str(limit_to_extruder)
        if (limit_to_extruder is not None and limit_to_extruder != "-1") and self.getMetaDataEntry("position") != str(limit_to_extruder):
            if str(limit_to_extruder) in self.getNextStack().extruders:
                result = self.getNextStack().extruders[str(limit_to_extruder)].getProperty(key, property_name, context)
                if result is not None:
                    context.popContainer()
                    return result

        result = super().getProperty(key, property_name, context)
        context.popContainer()
        return result

    @override(CuraContainerStack)
    def _getMachineDefinition(self) -> ContainerInterface:
        if not self.getNextStack():
            raise Exceptions.NoGlobalStackError("Extruder {id} is missing the next stack!".format(id = self.id))

        return self.getNextStack()._getMachineDefinition()

    @override(CuraContainerStack)
    def deserialize(self, contents: str, file_name: Optional[str] = None) -> None:
        super().deserialize(contents, file_name)
        stacks = ContainerRegistry.getInstance().findContainerStacks(id=self.getMetaDataEntry("machine", ""))
        if stacks:
            self.setNextStack(stacks[0])

    def _onPropertiesChanged(self, key, properties):
        # When there is a setting that is not settable per extruder that depends on a value from a setting that is,
        # we do not always get properly informed that we should re-evaluate the setting. So make sure to indicate
        # something changed for those settings.
        if not self.getNextStack():
            return #There are no global settings to depend on.
        definitions = self.getNextStack().definition.findDefinitions(key = key)
        if definitions:
            has_global_dependencies = False
            for relation in definitions[0].relations:
                if not getattr(relation.target, "settable_per_extruder", True):
                    has_global_dependencies = True
                    break

            if has_global_dependencies:
                self.getNextStack().propertiesChanged.emit(key, properties)

    def findDefaultVariant(self):
        # The default variant is defined in the machine stack and/or definition, so use the machine stack to find
        # the default variant.
        return self.getNextStack().findDefaultVariant()


extruder_stack_mime = MimeType(
    name = "application/x-cura-extruderstack",
    comment = "Cura Extruder Stack",
    suffixes = ["extruder.cfg"]
)

MimeTypeDatabase.addMimeType(extruder_stack_mime)
ContainerRegistry.addContainerTypeByName(ExtruderStack, "extruder_stack", extruder_stack_mime.name)
