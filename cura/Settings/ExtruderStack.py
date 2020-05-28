# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING, Optional

from PyQt5.QtCore import pyqtProperty, pyqtSignal

from UM.Decorators import override
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.Interfaces import ContainerInterface, PropertyEvaluationContext
from UM.Util import parseBool

import cura.CuraApplication

from . import Exceptions
from .CuraContainerStack import CuraContainerStack, _ContainerIndexes
from .ExtruderManager import ExtruderManager

if TYPE_CHECKING:
    from cura.Settings.GlobalStack import GlobalStack


class ExtruderStack(CuraContainerStack):
    """Represents an Extruder and its related containers."""

    def __init__(self, container_id: str) -> None:
        super().__init__(container_id)

        self.setMetaDataEntry("type", "extruder_train") # For backward compatibility

        self.propertiesChanged.connect(self._onPropertiesChanged)

    enabledChanged = pyqtSignal()

    @override(ContainerStack)
    def setNextStack(self, stack: CuraContainerStack, connect_signals: bool = True) -> None:
        """Overridden from ContainerStack
        
        This will set the next stack and ensure that we register this stack as an extruder.
        """

        super().setNextStack(stack)
        stack.addExtruder(self)
        self.setMetaDataEntry("machine", stack.id)

    @override(ContainerStack)
    def getNextStack(self) -> Optional["GlobalStack"]:
        return super().getNextStack()

    @pyqtProperty(int, constant = True)
    def position(self) -> int:
        return int(self.getMetaDataEntry("position"))

    def setEnabled(self, enabled: bool) -> None:
        if self.getMetaDataEntry("enabled", True) == enabled: # No change.
            return # Don't emit a signal then.
        self.setMetaDataEntry("enabled", str(enabled))
        self.enabledChanged.emit()

    @pyqtProperty(bool, notify = enabledChanged)
    def isEnabled(self) -> bool:
        return parseBool(self.getMetaDataEntry("enabled", "True"))

    @classmethod
    def getLoadingPriority(cls) -> int:
        return 3

    compatibleMaterialDiameterChanged = pyqtSignal()

    def getCompatibleMaterialDiameter(self) -> float:
        """Return the filament diameter that the machine requires.
        
        If the machine has no requirement for the diameter, -1 is returned.
        :return: The filament diameter for the printer
        """

        context = PropertyEvaluationContext(self)
        context.context["evaluate_from_container_index"] = _ContainerIndexes.Variant

        return float(self.getProperty("material_diameter", "value", context = context))

    def setCompatibleMaterialDiameter(self, value: float) -> None:
        old_approximate_diameter = self.getApproximateMaterialDiameter()
        if self.getCompatibleMaterialDiameter() != value:
            self.definitionChanges.setProperty("material_diameter", "value", value)
            self.compatibleMaterialDiameterChanged.emit()

            # Emit approximate diameter changed signal if needed
            if old_approximate_diameter != self.getApproximateMaterialDiameter():
                self.approximateMaterialDiameterChanged.emit()

    compatibleMaterialDiameter = pyqtProperty(float, fset = setCompatibleMaterialDiameter,
                                              fget = getCompatibleMaterialDiameter,
                                              notify = compatibleMaterialDiameterChanged)

    approximateMaterialDiameterChanged = pyqtSignal()

    def getApproximateMaterialDiameter(self) -> float:
        """Return the approximate filament diameter that the machine requires.
        
        The approximate material diameter is the material diameter rounded to
        the nearest millimetre.
        
        If the machine has no requirement for the diameter, -1 is returned.
        
        :return: The approximate filament diameter for the printer
        """

        return round(self.getCompatibleMaterialDiameter())

    approximateMaterialDiameter = pyqtProperty(float, fget = getApproximateMaterialDiameter,
                                               notify = approximateMaterialDiameterChanged)

    @override(ContainerStack)
    def getProperty(self, key: str, property_name: str, context: Optional[PropertyEvaluationContext] = None) -> Any:
        """Overridden from ContainerStack
        
        It will perform a few extra checks when trying to get properties.
        
        The two extra checks it currently does is to ensure a next stack is set and to bypass
        the extruder when the property is not settable per extruder.
        
        :throws Exceptions.NoGlobalStackError Raised when trying to get a property from an extruder without
        having a next stack set.
        """

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
            if limit_to_extruder == -1:
                limit_to_extruder = int(cura.CuraApplication.CuraApplication.getInstance().getMachineManager().defaultExtruderPosition)
            limit_to_extruder = str(limit_to_extruder)

        if (limit_to_extruder is not None and limit_to_extruder != "-1") and self.getMetaDataEntry("position") != str(limit_to_extruder):
            try:
                result = self.getNextStack().extruderList[int(limit_to_extruder)].getProperty(key, property_name, context)
                if result is not None:
                    context.popContainer()
                    return result
            except IndexError:
                pass

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
        if "enabled" not in self.getMetaData():
            self.setMetaDataEntry("enabled", "True")

    def _onPropertiesChanged(self, key: str, properties: Dict[str, Any]) -> None:
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


extruder_stack_mime = MimeType(
    name = "application/x-cura-extruderstack",
    comment = "Cura Extruder Stack",
    suffixes = ["extruder.cfg"]
)

MimeTypeDatabase.addMimeType(extruder_stack_mime)
ContainerRegistry.addContainerTypeByName(ExtruderStack, "extruder_stack", extruder_stack_mime.name)
