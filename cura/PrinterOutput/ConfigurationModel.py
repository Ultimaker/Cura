# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtProperty, QObject, pyqtSignal


class ConfigurationModel(QObject):

    configurationChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._printer_type = None
        self._extruder_configurations = []
        self._buildplate_configuration = None

    def setPrinterType(self, printer_type):
        self._printer_type = printer_type

    @pyqtProperty(str, fset = setPrinterType, constant = True)
    def printerType(self):
        return self._printer_type

    def setExtruderConfigurations(self, extruder_configurations):
        self._extruder_configurations = extruder_configurations

    @pyqtProperty("QVariantList", fset = setExtruderConfigurations, notify = configurationChanged)
    def extruderConfigurations(self):
        return self._extruder_configurations

    def setBuildplateConfiguration(self, buildplate_configuration):
        self._buildplate_configuration = buildplate_configuration

    @pyqtProperty(str, fset = setBuildplateConfiguration, notify = configurationChanged)
    def buildplateConfiguration(self):
        return self._buildplate_configuration

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        extruder_hash = hash(0)
        for configuration in self.extruderConfigurations:
            extruder_hash ^= hash(frozenset(configuration.items()))
        return hash(self.printerType) ^ extruder_hash ^ hash(self.buildplateConfiguration)