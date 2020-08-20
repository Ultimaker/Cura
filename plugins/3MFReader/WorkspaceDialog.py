# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import pyqtSignal, QObject, pyqtProperty, QCoreApplication
from UM.FlameProfiler import pyqtSlot
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

import os
import threading
import time
i18n_catalog = i18nCatalog("cura")


class WorkspaceDialog(QObject):
    showDialogSignal = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self._component = None
        self._context = None
        self._view = None
        self._qml_url = "WorkspaceDialog.qml"
        self._lock = threading.Lock()
        self._default_strategy = None
        self._result = {"machine": self._default_strategy,
                        "quality_changes": self._default_strategy,
                        "definition_changes": self._default_strategy,
                        "material": self._default_strategy}
        self._visible = False
        self.showDialogSignal.connect(self.__show)

        self._has_quality_changes_conflict = False
        self._has_definition_changes_conflict = False
        self._has_machine_conflict = False
        self._has_material_conflict = False
        self._has_visible_settings_field = False
        self._num_visible_settings = 0
        self._num_user_settings = 0
        self._active_mode = ""
        self._quality_name = ""
        self._num_settings_overridden_by_quality_changes = 0
        self._quality_type = ""
        self._intent_name = ""
        self._machine_name = ""
        self._machine_type = ""
        self._variant_type = ""
        self._material_labels = []
        self._extruders = []
        self._objects_on_plate = False
        self._is_printer_group = False

    machineConflictChanged = pyqtSignal()
    qualityChangesConflictChanged = pyqtSignal()
    materialConflictChanged = pyqtSignal()
    numVisibleSettingsChanged = pyqtSignal()
    activeModeChanged = pyqtSignal()
    qualityNameChanged = pyqtSignal()
    hasVisibleSettingsFieldChanged = pyqtSignal()
    numSettingsOverridenByQualityChangesChanged = pyqtSignal()
    qualityTypeChanged = pyqtSignal()
    intentNameChanged = pyqtSignal()
    machineNameChanged = pyqtSignal()
    materialLabelsChanged = pyqtSignal()
    objectsOnPlateChanged = pyqtSignal()
    numUserSettingsChanged = pyqtSignal()
    machineTypeChanged = pyqtSignal()
    variantTypeChanged = pyqtSignal()
    extrudersChanged = pyqtSignal()
    isPrinterGroupChanged = pyqtSignal()

    @pyqtProperty(bool, notify = isPrinterGroupChanged)
    def isPrinterGroup(self) -> bool:
        return self._is_printer_group

    def setIsPrinterGroup(self, value: bool):
        if value != self._is_printer_group:
            self._is_printer_group = value
            self.isPrinterGroupChanged.emit()

    @pyqtProperty(str, notify=variantTypeChanged)
    def variantType(self):
        return self._variant_type

    def setVariantType(self, variant_type):
        if self._variant_type != variant_type:
            self._variant_type = variant_type
            self.variantTypeChanged.emit()

    @pyqtProperty(str, notify=machineTypeChanged)
    def machineType(self):
        return self._machine_type

    def setMachineType(self, machine_type):
        self._machine_type = machine_type
        self.machineTypeChanged.emit()

    def setNumUserSettings(self, num_user_settings):
        if self._num_user_settings != num_user_settings:
            self._num_user_settings = num_user_settings
            self.numVisibleSettingsChanged.emit()

    @pyqtProperty(int, notify=numUserSettingsChanged)
    def numUserSettings(self):
        return self._num_user_settings

    @pyqtProperty(bool, notify=objectsOnPlateChanged)
    def hasObjectsOnPlate(self):
        return self._objects_on_plate

    def setHasObjectsOnPlate(self, objects_on_plate):
        if self._objects_on_plate != objects_on_plate:
            self._objects_on_plate = objects_on_plate
            self.objectsOnPlateChanged.emit()

    @pyqtProperty("QVariantList", notify = materialLabelsChanged)
    def materialLabels(self):
        return self._material_labels

    def setMaterialLabels(self, material_labels):
        if self._material_labels != material_labels:
            self._material_labels = material_labels
            self.materialLabelsChanged.emit()

    @pyqtProperty("QVariantList", notify=extrudersChanged)
    def extruders(self):
        return self._extruders

    def setExtruders(self, extruders):
        if self._extruders != extruders:
            self._extruders = extruders
            self.extrudersChanged.emit()

    @pyqtProperty(str, notify = machineNameChanged)
    def machineName(self):
        return self._machine_name

    def setMachineName(self, machine_name):
        if self._machine_name != machine_name:
            self._machine_name = machine_name
            self.machineNameChanged.emit()

    @pyqtProperty(str, notify=qualityTypeChanged)
    def qualityType(self):
        return self._quality_type

    def setQualityType(self, quality_type):
        if self._quality_type != quality_type:
            self._quality_type = quality_type
            self.qualityTypeChanged.emit()

    @pyqtProperty(int, notify=numSettingsOverridenByQualityChangesChanged)
    def numSettingsOverridenByQualityChanges(self):
        return self._num_settings_overridden_by_quality_changes

    def setNumSettingsOverriddenByQualityChanges(self, num_settings_overridden_by_quality_changes):
        self._num_settings_overridden_by_quality_changes = num_settings_overridden_by_quality_changes
        self.numSettingsOverridenByQualityChangesChanged.emit()

    @pyqtProperty(str, notify=qualityNameChanged)
    def qualityName(self):
        return self._quality_name

    def setQualityName(self, quality_name):
        if self._quality_name != quality_name:
            self._quality_name = quality_name
            self.qualityNameChanged.emit()

    @pyqtProperty(str, notify = intentNameChanged)
    def intentName(self) -> str:
        return self._intent_name

    def setIntentName(self, intent_name: str) -> None:
        if self._intent_name != intent_name:
            self._intent_name = intent_name
            self.intentNameChanged.emit()

    @pyqtProperty(str, notify=activeModeChanged)
    def activeMode(self):
        return self._active_mode

    def setActiveMode(self, active_mode):
        if active_mode == 0:
            self._active_mode = i18n_catalog.i18nc("@title:tab", "Recommended")
        else:
            self._active_mode = i18n_catalog.i18nc("@title:tab", "Custom")
        self.activeModeChanged.emit()

    @pyqtProperty(int, notify = hasVisibleSettingsFieldChanged)
    def hasVisibleSettingsField(self):
        return self._has_visible_settings_field

    def setHasVisibleSettingsField(self, has_visible_settings_field):
        self._has_visible_settings_field = has_visible_settings_field
        self.hasVisibleSettingsFieldChanged.emit()

    @pyqtProperty(int, constant = True)
    def totalNumberOfSettings(self):
        general_definition_containers = ContainerRegistry.getInstance().findDefinitionContainers(id = "fdmprinter")
        if not general_definition_containers:
            return 0
        return len(general_definition_containers[0].getAllKeys())

    @pyqtProperty(int, notify = numVisibleSettingsChanged)
    def numVisibleSettings(self):
        return self._num_visible_settings

    def setNumVisibleSettings(self, num_visible_settings):
        if self._num_visible_settings != num_visible_settings:
            self._num_visible_settings = num_visible_settings
            self.numVisibleSettingsChanged.emit()

    @pyqtProperty(bool, notify = machineConflictChanged)
    def machineConflict(self):
        return self._has_machine_conflict

    @pyqtProperty(bool, notify=qualityChangesConflictChanged)
    def qualityChangesConflict(self):
        return self._has_quality_changes_conflict

    @pyqtProperty(bool, notify=materialConflictChanged)
    def materialConflict(self):
        return self._has_material_conflict

    @pyqtSlot(str, str)
    def setResolveStrategy(self, key, strategy):
        if key in self._result:
            self._result[key] = strategy

    @pyqtSlot()
    def closeBackend(self):
        """Close the backend: otherwise one could end up with "Slicing..."""

        Application.getInstance().getBackend().close()

    def setMaterialConflict(self, material_conflict):
        if self._has_material_conflict != material_conflict:
            self._has_material_conflict = material_conflict
            self.materialConflictChanged.emit()

    def setMachineConflict(self, machine_conflict):
        if self._has_machine_conflict != machine_conflict:
            self._has_machine_conflict = machine_conflict
            self.machineConflictChanged.emit()

    def setQualityChangesConflict(self, quality_changes_conflict):
        if self._has_quality_changes_conflict != quality_changes_conflict:
            self._has_quality_changes_conflict = quality_changes_conflict
            self.qualityChangesConflictChanged.emit()

    def getResult(self):
        if "machine" in self._result and not self._has_machine_conflict:
            self._result["machine"] = None
        if "quality_changes" in self._result and not self._has_quality_changes_conflict:
            self._result["quality_changes"] = None
        if "material" in self._result and not self._has_material_conflict:
            self._result["material"] = None

        # If the machine needs to be re-created, the definition_changes should also be re-created.
        # If the machine strategy is None, it means that there is no name conflict with existing ones. In this case
        # new definitions changes are created
        if "machine" in self._result:
            if self._result["machine"] == "new" or self._result["machine"] is None and self._result["definition_changes"] is None:
                self._result["definition_changes"] = "new"

        return self._result

    def _createViewFromQML(self):
        path = os.path.join(PluginRegistry.getInstance().getPluginPath("3MFReader"), self._qml_url)
        self._view = Application.getInstance().createQmlComponent(path, {"manager": self})

    def show(self):
        # Emit signal so the right thread actually shows the view.
        if threading.current_thread() != threading.main_thread():
            self._lock.acquire()
        # Reset the result
        self._result = {"machine": self._default_strategy,
                        "quality_changes": self._default_strategy,
                        "definition_changes": self._default_strategy,
                        "material": self._default_strategy}
        self._visible = True
        self.showDialogSignal.emit()

    @pyqtSlot()
    def notifyClosed(self):
        """Used to notify the dialog so the lock can be released."""

        self._result = {} # The result should be cleared before hide, because after it is released the main thread lock
        self._visible = False
        try:
            self._lock.release()
        except:
            pass

    def hide(self):
        self._visible = False
        self._view.hide()
        try:
            self._lock.release()
        except:
            pass

    @pyqtSlot(bool)
    def _onVisibilityChanged(self, visible):
        if not visible:
            try:
                self._lock.release()
            except:
                pass

    @pyqtSlot()
    def onOkButtonClicked(self):
        self._view.hide()
        self.hide()

    @pyqtSlot()
    def onCancelButtonClicked(self):
        self._result = {}
        self._view.hide()
        self.hide()

    def waitForClose(self):
        """Block thread until the dialog is closed."""

        if self._visible:
            if threading.current_thread() != threading.main_thread():
                self._lock.acquire()
                self._lock.release()
            else:
                # If this is not run from a separate thread, we need to ensure that the events are still processed.
                while self._visible:
                    time.sleep(1 / 50)
                    QCoreApplication.processEvents()  # Ensure that the GUI does not freeze.

    def __show(self):
        if self._view is None:
            self._createViewFromQML()
        if self._view:
            self._view.show()
