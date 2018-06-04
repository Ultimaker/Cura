# Copyright (c) 2018 fieldOfView
# The Blackbelt plugin is released under the terms of the LGPLv3 or higher.

from UM.Application import Application
from UM.Settings.ContainerRegistry import ContainerRegistry

from PyQt5.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QObject

import json
import re

## QML-accessible singleton for access to extended data on definition and variants
class BlackBeltSingleton(QObject):
    def __init__(self):
        super().__init__()

        self._application = Application.getInstance()
        self._machine_manager = self._application.getMachineManager()
        self._global_container_stack = None

        self._variants_terms_pattern = ""
        self._variants_terms = []

        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)
        self._onGlobalContainerStackChanged(emit = False)
        self._machine_manager.activeVariantChanged.connect(self._onActiveVariantChanged)
        self._onActiveVariantChanged(emit = False)

    def _onGlobalContainerStackChanged(self, emit = True):
        self._global_container_stack = self._application.getGlobalContainerStack()
        if not self._global_container_stack:
            return

        self._variants_terms_pattern = self._global_container_stack.getMetaDataEntry("variants_id_pattern", "")
        self._variants_terms_pattern = self._variants_terms_pattern.replace("{definition_id}", self._global_container_stack.getBottom().getId())
        self._variants_terms_pattern = self._variants_terms_pattern.replace("{term}", "(.*?)")

        if emit:
            self.activeMachineChanged.emit()

    def _onActiveVariantChanged(self, emit = True):
        if not self._global_container_stack:
            return

        active_variant_id = self._global_container_stack.variant.getId()

        result = re.match("^%s$" % self._variants_terms_pattern, active_variant_id)
        if result:
            self._variants_terms = list(result.groups())
        else:
            self._variants_terms = []

        if emit:
            self.activeVariantChanged.emit()

    activeMachineChanged = pyqtSignal()
    activeVariantChanged = pyqtSignal()

    @pyqtProperty(str, notify = activeMachineChanged)
    def variantsTerms(self):
        if not self._global_container_stack:
            return "[]"
        return json.dumps(self._global_container_stack.getMetaDataEntry("variants_terms", []))

    @pyqtProperty("QVariantList", notify = activeVariantChanged)
    def activeVariantTerms(self):
        return self._variants_terms

    @pyqtSlot(int, str)
    def setActiveVariantTerm(self, index, term):
        if not self._global_container_stack:
            return

        self._variants_terms[index] = term
        variant_id = self._variants_terms_pattern.replace("(.*?)", "%s") % tuple(self._variants_terms)
        containers = ContainerRegistry.getInstance().findContainers(id = variant_id, type = "variant")
        if containers:
            self._global_container_stack.extruders["0"].setVariant(containers[0])


    ##  Get the singleton instance for this class.
    @classmethod
    def getInstance(cls, engine = None, script_engine = None):
        # Note: Explicit use of class name to prevent issues with inheritance.
        if not BlackBeltSingleton.__instance:
            BlackBeltSingleton.__instance = cls()
        return BlackBeltSingleton.__instance

    __instance = None   # type: "BlackBeltSingleton"
