# Copyright (c) 2022 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt6.QtCore import pyqtSignal, QObject, pyqtProperty, QCoreApplication, QUrl
from PyQt6.QtGui import QDesktopServices
from typing import List, Optional, Dict, cast

from cura.Machines.Models.MachineListModel import MachineListModel
from cura.Machines.Models.IntentTranslations import intent_translations
from cura.Settings.GlobalStack import GlobalStack
from UM.Application import Application
from UM.FlameProfiler import pyqtSlot
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Settings.ContainerRegistry import ContainerRegistry

import os
import threading
import time

from cura.CuraApplication import CuraApplication

from .SpecificSettingsModel import SpecificSettingsModel

i18n_catalog = i18nCatalog("cura")


class WorkspaceDialog(QObject):
    showDialogSignal = pyqtSignal()

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self._component = None
        self._context = None
        self._view = None
        self._qml_url = "WorkspaceDialog.qml"
        self._lock = threading.Lock()
        self._default_strategy = None
        self._result = {
            "machine": self._default_strategy,
            "quality_changes": self._default_strategy,
            "definition_changes": self._default_strategy,
            "material": self._default_strategy,
        }
        self._override_machine = None
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
        self._current_machine_name = ""
        self._material_labels = []
        self._extruders = []
        self._objects_on_plate = False
        self._is_printer_group = False
        self._updatable_machines_model = MachineListModel(self, listenToChanges = False, showCloudPrinters = True)
        self._missing_package_metadata: List[Dict[str, str]] = []
        self._plugin_registry: PluginRegistry = CuraApplication.getInstance().getPluginRegistry()
        self._install_missing_package_dialog: Optional[QObject] = None
        self._is_abstract_machine = False
        self._is_networked_machine = False
        self._is_compatible_machine = False
        self._allow_create_machine = True
        self._exported_settings_model = SpecificSettingsModel()
        self._exported_settings_model.modelChanged.connect(self.exportedSettingModelChanged.emit)
        self._current_machine_pos_index = 0
        self._is_ucp = False

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
    updatableMachinesChanged = pyqtSignal()
    isAbstractMachineChanged = pyqtSignal()
    isNetworkedChanged = pyqtSignal()
    materialLabelsChanged = pyqtSignal()
    objectsOnPlateChanged = pyqtSignal()
    numUserSettingsChanged = pyqtSignal()
    machineTypeChanged = pyqtSignal()
    variantTypeChanged = pyqtSignal()
    extrudersChanged = pyqtSignal()
    isPrinterGroupChanged = pyqtSignal()
    missingPackagesChanged = pyqtSignal()
    isCompatibleMachineChanged = pyqtSignal()
    isUcpChanged = pyqtSignal()
    exportedSettingModelChanged = pyqtSignal()

    @pyqtProperty(bool, notify = isPrinterGroupChanged)
    def isPrinterGroup(self) -> bool:
        return self._is_printer_group

    def setIsPrinterGroup(self, value: bool):
        if value != self._is_printer_group:
            self._is_printer_group = value
            self.isPrinterGroupChanged.emit()

    @pyqtProperty(str, notify=variantTypeChanged)
    def variantType(self) -> str:
        return self._variant_type

    def setVariantType(self, variant_type: str) -> None:
        if self._variant_type != variant_type:
            self._variant_type = variant_type
            self.variantTypeChanged.emit()

    @pyqtProperty(str, notify=machineTypeChanged)
    def machineType(self) -> str:
        return self._machine_type

    def setMachineType(self, machine_type: str) -> None:
        self._machine_type = machine_type
        self.machineTypeChanged.emit()

    def setNumUserSettings(self, num_user_settings: int) -> None:
        if self._num_user_settings != num_user_settings:
            self._num_user_settings = num_user_settings
            self.numVisibleSettingsChanged.emit()

    @pyqtProperty(int, notify=numUserSettingsChanged)
    def numUserSettings(self) -> int:
        return self._num_user_settings

    @pyqtProperty(bool, notify=objectsOnPlateChanged)
    def hasObjectsOnPlate(self) -> bool:
        return self._objects_on_plate

    def setHasObjectsOnPlate(self, objects_on_plate):
        if self._objects_on_plate != objects_on_plate:
            self._objects_on_plate = objects_on_plate
            self.objectsOnPlateChanged.emit()

    @pyqtProperty("QVariantList", notify = materialLabelsChanged)
    def materialLabels(self) -> List[str]:
        return self._material_labels

    def setMaterialLabels(self, material_labels: List[str]) -> None:
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
    def machineName(self) -> str:
        return self._machine_name

    def setMachineName(self, machine_name: str) -> None:
        if self._machine_name != machine_name:
            self._machine_name = machine_name
            self.machineNameChanged.emit()

    def setCurrentMachineName(self, machine: str) -> None:
        self._current_machine_name = machine

    @pyqtProperty(str, notify = machineNameChanged)
    def currentMachineName(self) -> str:
        return self._current_machine_name

    @staticmethod
    def getIndexOfCurrentMachine(list_of_dicts, key, value, defaultIndex):
        for i, d in enumerate(list_of_dicts):
            if d.get(key) == value:  # found the dictionary
                return i
        return defaultIndex

    @pyqtProperty(int, notify = machineNameChanged)
    def currentMachinePositionIndex(self):
        return self._current_machine_pos_index

    @pyqtProperty(QObject, notify = updatableMachinesChanged)
    def updatableMachinesModel(self) -> MachineListModel:
        if self._current_machine_name != "":
            self._current_machine_pos_index = self.getIndexOfCurrentMachine(self._updatable_machines_model.getItems(), "id", self._current_machine_name, defaultIndex = 0)
        else:
            self._current_machine_pos_index = 0
        return cast(MachineListModel, self._updatable_machines_model)

    def setUpdatableMachines(self, updatable_machines: List[GlobalStack]) -> None:
        self._updatable_machines_model.set_machines_filter(updatable_machines)
        self.updatableMachinesChanged.emit()

    @pyqtProperty(bool, notify = isAbstractMachineChanged)
    def isAbstractMachine(self) -> bool:
        return self._is_abstract_machine

    @pyqtSlot(bool)
    def setIsAbstractMachine(self, is_abstract_machine: bool) -> None:
        self._is_abstract_machine = is_abstract_machine
        self.isAbstractMachineChanged.emit()

    @pyqtProperty(bool, notify = isNetworkedChanged)
    def isNetworked(self) -> bool:
        return self._is_networked_machine

    @pyqtSlot(bool)
    def setIsNetworkedMachine(self, is_networked_machine: bool) -> None:
        self._is_networked_machine = is_networked_machine
        self.isNetworkedChanged.emit()

    @pyqtProperty(str, notify=qualityTypeChanged)
    def qualityType(self) -> str:
        return self._quality_type

    def setQualityType(self, quality_type: str) -> None:
        if self._quality_type != quality_type:
            self._quality_type = quality_type
            self.qualityTypeChanged.emit()

    @pyqtProperty(int, notify=numSettingsOverridenByQualityChangesChanged)
    def numSettingsOverridenByQualityChanges(self) -> int:
        return self._num_settings_overridden_by_quality_changes

    def setNumSettingsOverriddenByQualityChanges(self, num_settings_overridden_by_quality_changes: int) -> None:
        self._num_settings_overridden_by_quality_changes = num_settings_overridden_by_quality_changes
        self.numSettingsOverridenByQualityChangesChanged.emit()

    @pyqtProperty(str, notify=qualityNameChanged)
    def qualityName(self) -> str:
        return self._quality_name

    def setQualityName(self, quality_name: str) -> None:
        if self._quality_name != quality_name:
            self._quality_name = quality_name
            self.qualityNameChanged.emit()

    @pyqtProperty(str, notify = intentNameChanged)
    def intentName(self) -> str:
        return self._intent_name

    def setIntentName(self, intent_name: str) -> None:
        if self._intent_name != intent_name:
            try:
                 self._intent_name = intent_translations[intent_name]["name"]
            except:
                self._intent_name = intent_name.title()
            self.intentNameChanged.emit()

        if not self._intent_name:
            self._intent_name = intent_translations["default"]["name"]
            self.intentNameChanged.emit()

    @pyqtProperty(str, notify=activeModeChanged)
    def activeMode(self) -> str:
        return self._active_mode

    def setActiveMode(self, active_mode: int) -> None:
        if active_mode == 0:
            self._active_mode = i18n_catalog.i18nc("@title:tab", "Recommended")
        else:
            self._active_mode = i18n_catalog.i18nc("@title:tab", "Custom")
        self.activeModeChanged.emit()

    @pyqtProperty(bool, notify = hasVisibleSettingsFieldChanged)
    def hasVisibleSettingsField(self) -> bool:
        return self._has_visible_settings_field

    def setHasVisibleSettingsField(self, has_visible_settings_field: bool) -> None:
        self._has_visible_settings_field = has_visible_settings_field
        self.hasVisibleSettingsFieldChanged.emit()

    @pyqtProperty(int, constant = True)
    def totalNumberOfSettings(self) -> int:
        general_definition_containers = ContainerRegistry.getInstance().findDefinitionContainers(id = "fdmprinter")
        if not general_definition_containers:
            return 0
        return len(general_definition_containers[0].getAllKeys())

    @pyqtProperty(int, notify = numVisibleSettingsChanged)
    def numVisibleSettings(self) -> int:
        return self._num_visible_settings

    def setNumVisibleSettings(self, num_visible_settings: int) -> None:
        if self._num_visible_settings != num_visible_settings:
            self._num_visible_settings = num_visible_settings
            self.numVisibleSettingsChanged.emit()

    @pyqtProperty(bool, notify = machineConflictChanged)
    def machineConflict(self) -> bool:
        return self._has_machine_conflict

    @pyqtProperty(bool, notify=qualityChangesConflictChanged)
    def qualityChangesConflict(self) -> bool:
        return self._has_quality_changes_conflict

    @pyqtProperty(bool, notify=materialConflictChanged)
    def materialConflict(self) -> bool:
        return self._has_material_conflict

    @pyqtSlot(str, str)
    def setResolveStrategy(self, key: str, strategy: Optional[str]) -> None:
        if key in self._result:
            self._result[key] = strategy

    def getMachineToOverride(self) -> str:
        return self._override_machine

    @pyqtSlot(str)
    def setMachineToOverride(self, machine_name: str) -> None:
        self._override_machine = machine_name
        self.updateCompatibleMachine()

    def updateCompatibleMachine(self):
        registry = ContainerRegistry.getInstance()
        containers_expected = registry.findDefinitionContainers(name=self._machine_type)
        containers_selected = registry.findContainerStacks(id=self._override_machine)
        if len(containers_expected) == 1 and len(containers_selected) == 1:
            new_compatible_machine = (containers_expected[0] == containers_selected[0].definition)
            if new_compatible_machine != self._is_compatible_machine:
                self._is_compatible_machine = new_compatible_machine
                self.isCompatibleMachineChanged.emit()

    @pyqtProperty(bool, notify = isCompatibleMachineChanged)
    def isCompatibleMachine(self) -> bool:
        return self._is_compatible_machine

    def setIsUcp(self, isUcp: bool) -> None:
        if isUcp != self._is_ucp:
            self._is_ucp = isUcp
            self.isUcpChanged.emit()

    @pyqtProperty(bool, notify=isUcpChanged)
    def isUcp(self):
        return self._is_ucp

    def setAllowCreatemachine(self, allow_create_machine):
        self._allow_create_machine = allow_create_machine

    @pyqtProperty(bool, constant = True)
    def allowCreateMachine(self):
        return self._allow_create_machine

    @pyqtProperty(QObject, notify=exportedSettingModelChanged)
    def exportedSettingModel(self):
        return self._exported_settings_model

    @pyqtProperty("QVariantList", notify=exportedSettingModelChanged)
    def exportedSettingModelItems(self):
        return self._exported_settings_model.items

    @pyqtProperty(int, notify=exportedSettingModelChanged)
    def exportedSettingModelRowCount(self):
        return self._exported_settings_model.rowCount()
    @pyqtSlot()
    def closeBackend(self) -> None:
        """Close the backend: otherwise one could end up with "Slicing..."""

        Application.getInstance().getBackend().close()

    def setMaterialConflict(self, material_conflict: bool) -> None:
        if self._has_material_conflict != material_conflict:
            self._has_material_conflict = material_conflict
            self.materialConflictChanged.emit()

    def setMachineConflict(self, machine_conflict: bool) -> None:
        if self._has_machine_conflict != machine_conflict:
            self._has_machine_conflict = machine_conflict
            self.machineConflictChanged.emit()

    def setQualityChangesConflict(self, quality_changes_conflict: bool) -> None:
        if self._has_quality_changes_conflict != quality_changes_conflict:
            self._has_quality_changes_conflict = quality_changes_conflict
            self.qualityChangesConflictChanged.emit()

    def setMissingPackagesMetadata(self, missing_package_metadata: List[Dict[str, str]]) -> None:
        self._missing_package_metadata = missing_package_metadata
        self.missingPackagesChanged.emit()

    @pyqtProperty("QVariantList", notify=missingPackagesChanged)
    def missingPackages(self) -> List[Dict[str, str]]:
        return self._missing_package_metadata

    @pyqtSlot()
    def installMissingPackages(self) -> None:
        marketplace_plugin = PluginRegistry.getInstance().getPluginObject("Marketplace")
        if not marketplace_plugin:
            Logger.warning("Could not show dialog to install missing plug-ins. Is Marketplace plug-in not available?")
        marketplace_plugin.showInstallMissingPackageDialog(self._missing_package_metadata, self.showMissingMaterialsWarning)  # type: ignore

    def getResult(self) -> Dict[str, Optional[str]]:
        if "machine" in self._result and self.updatableMachinesModel.count <= 1:
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

    def _createViewFromQML(self) -> None:
        three_mf_reader_path = PluginRegistry.getInstance().getPluginPath("3MFReader")
        if three_mf_reader_path:
            path = os.path.join(three_mf_reader_path, self._qml_url)
            self._view = CuraApplication.getInstance().createQmlComponent(path, {"manager": self})

    def show(self) -> None:
        # Emit signal so the right thread actually shows the view.
        if threading.current_thread() != threading.main_thread():
            self._lock.acquire()
        # Reset the result
        self._result = {
            "machine": self._default_strategy,
            "quality_changes": self._default_strategy,
            "definition_changes": self._default_strategy,
            "material": self._default_strategy,
        }
        self._visible = True
        self.showDialogSignal.emit()

    @pyqtSlot()
    def notifyClosed(self) -> None:
        """Used to notify the dialog so the lock can be released."""

        self._result = {} # The result should be cleared before hide, because after it is released the main thread lock
        self._visible = False
        try:
            self._lock.release()
        except:
            pass

    def hide(self) -> None:
        self._visible = False
        self._view.hide()
        try:
            self._lock.release()
        except:
            pass

    @pyqtSlot(bool)
    def _onVisibilityChanged(self, visible: bool) -> None:
        if not visible:
            try:
                self._lock.release()
            except:
                pass

    @pyqtSlot()
    def onOkButtonClicked(self) -> None:
        self._view.hide()
        self.hide()

    @pyqtSlot()
    def onCancelButtonClicked(self) -> None:
        self._result = {}
        self._view.hide()
        self.hide()

    def waitForClose(self) -> None:
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

    @pyqtSlot()
    def showMissingMaterialsWarning(self) -> None:
        result_message = Message(
            i18n_catalog.i18nc("@info:status",
                               "Some of the packages used in the project file are currently not installed in Cura, this might produce undesirable print results. We highly recommend installing the all required packages from the Marketplace."),
            lifetime=0,
            title=i18n_catalog.i18nc("@info:title", "Some required packages are not installed"),
            message_type=Message.MessageType.WARNING
        )
        result_message.addAction(
            "learn_more",
            name=i18n_catalog.i18nc("@action:button", "Learn more"),
            icon="",
            description=i18n_catalog.i18nc("@label", "Learn more about project packages."),
            button_align=Message.ActionButtonAlignment.ALIGN_LEFT,
            button_style=Message.ActionButtonStyle.LINK
        )
        result_message.addAction(
            "install_packages",
            name=i18n_catalog.i18nc("@action:button", "Install Packages"),
            icon="",
            description=i18n_catalog.i18nc("@label", "Install missing packages from project file."),
            button_align=Message.ActionButtonAlignment.ALIGN_RIGHT,
            button_style=Message.ActionButtonStyle.DEFAULT
        )
        result_message.actionTriggered.connect(self._onMessageActionTriggered)
        result_message.show()

    def _onMessageActionTriggered(self, message: Message, sync_message_action: str) -> None:
        if sync_message_action == "install_materials":
            self.installMissingPackages()
            message.hide()
        elif sync_message_action == "learn_more":
            QDesktopServices.openUrl(QUrl("https://support.ultimaker.com/hc/en-us/articles/360011968360-Using-the-Ultimaker-Marketplace"))


    def __show(self) -> None:
        if self._view is None:
            self._createViewFromQML()
        if self._view:
            self._view.show()
