# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import QObject, pyqtSlot #To expose data to QML.

from cura.Settings.ContainerManager import ContainerManager
from UM.Logger import Logger
from UM.Message import Message #To create a warning message about material diameter.
from UM.i18n import i18nCatalog #Translated strings.

catalog = i18nCatalog("cura")

##  Handles material-related data, processing requests to change them and
#   providing data for the GUI.
#
#   TODO: Move material-related managing over from the machine manager to here.
class MaterialManager(QObject):
    ##  Creates the global values for the material manager to use.
    def __init__(self, parent = None):
        super().__init__(parent)

        #Material diameter changed warning message.
        self._material_diameter_warning_message = Message(catalog.i18nc("@info:status Has a cancel button next to it.",
            "The selected material diameter causes the material to become incompatible with the current printer."), title = catalog.i18nc("@info:title", "Incompatible Material"))
        self._material_diameter_warning_message.addAction("Undo", catalog.i18nc("@action:button", "Undo"), None, catalog.i18nc("@action", "Undo changing the material diameter."))
        self._material_diameter_warning_message.actionTriggered.connect(self._materialWarningMessageAction)

    ##  Creates an instance of the MaterialManager.
    #
    #   This should only be called by PyQt to create the singleton instance of
    #   this class.
    @staticmethod
    def createMaterialManager(engine = None, script_engine = None):
        return MaterialManager()

    @pyqtSlot(str, str)
    def showMaterialWarningMessage(self, material_id, previous_diameter):
        self._material_diameter_warning_message.previous_diameter = previous_diameter #Make sure that the undo button can properly undo the action.
        self._material_diameter_warning_message.material_id = material_id
        self._material_diameter_warning_message.show()

    ##  Called when clicking "undo" on the warning dialogue for disappeared
    #   materials.
    #
    #   This executes the undo action, restoring the material diameter.
    #
    #   \param button The identifier of the button that was pressed.
    def _materialWarningMessageAction(self, message, button):
        if button == "Undo":
            container_manager = ContainerManager.getInstance()
            container_manager.setContainerMetaDataEntry(self._material_diameter_warning_message.material_id, "properties/diameter", self._material_diameter_warning_message.previous_diameter)
            approximate_previous_diameter = str(round(float(self._material_diameter_warning_message.previous_diameter)))
            container_manager.setContainerMetaDataEntry(self._material_diameter_warning_message.material_id, "approximate_diameter", approximate_previous_diameter)
            container_manager.setContainerProperty(self._material_diameter_warning_message.material_id, "material_diameter", "value", self._material_diameter_warning_message.previous_diameter);
            message.hide()
        else:
            Logger.log("w", "Unknown button action for material diameter warning message: {action}".format(action = button))