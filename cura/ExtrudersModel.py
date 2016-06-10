# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty

import cura.ExtruderManager
import UM.Qt.ListModel

##  Model that holds extruders.
#
#   This model is designed for use by any list of extruders, but specifically
#   intended for drop-down lists of the current machine's extruders in place of
#   settings.
class ExtrudersModel(UM.Qt.ListModel.ListModel):
    # The ID of the container stack for the extruder.
    IdRole = Qt.UserRole + 1

    ##  Human-readable name of the extruder.
    NameRole = Qt.UserRole + 2

    ##  Colour of the material loaded in the extruder.
    ColourRole = Qt.UserRole + 3

    ##  Index of the extruder, which is also the value of the setting itself.
    #
    #   An index of 0 indicates the first extruder, an index of 1 the second
    #   one, and so on. This is the value that will be saved in instance
    #   containers.
    IndexRole = Qt.UserRole + 4

    ##  Colour to display if there is no material or the material has no known
    #   colour.
    defaultColour = "#FFFF00"

    ##  Initialises the extruders model, defining the roles and listening for
    #   changes in the data.
    #
    #   \param parent Parent QtObject of this list.
    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ColourRole, "colour")
        self.addRoleName(self.IndexRole, "index")

        self._add_global = False

        #Listen to changes.
        manager = cura.ExtruderManager.ExtruderManager.getInstance()
        manager.extrudersChanged.connect(self._updateExtruders) #When the list of extruders changes in general.
        UM.Application.globalContainerStackChanged.connect(self._updateExtruders) #When the current machine changes.
        self._updateExtruders()

    def setAddGlobal(self, add):
        if add != self._add_global:
            self._add_global = add
            self._updateExtruders()
            self.addGlobalChanged.emit()

    addGlobalChanged = pyqtSignal()
    @pyqtProperty(bool, fset = setAddGlobal, notify = addGlobalChanged)
    def addGlobal(self):
        return self._add_global

    ##  Update the list of extruders.
    #
    #   This should be called whenever the list of extruders changes.
    def _updateExtruders(self):
        self.clear()
        manager = cura.ExtruderManager.ExtruderManager.getInstance()
        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        if not global_container_stack:
            return #There is no machine to get the extruders of.

        if self._add_global:
            material = global_container_stack.findContainer({ "type": "material" })
            colour = material.getMetaDataEntry("color_code", default = self.defaultColour) if material else self.defaultColour
            item = {
                "id": global_container_stack.getId(),
                "name": "Global",
                "colour": colour,
                "index": -1
            }
            self.appendItem(item)

        for extruder in manager.getMachineExtruders(global_container_stack.getBottom().getId()):
            material = extruder.findContainer({ "type": "material" })
            colour = material.getMetaDataEntry("color_code", default = self.defaultColour) if material else self.defaultColour
            position = extruder.getBottom().getMetaDataEntry("position", default = "0") #Position in the definition.
            try:
                position = int(position)
            except ValueError: #Not a proper int.
                position = -1
            item = { #Construct an item with only the relevant information.
                "id": extruder.getId(),
                "name": extruder.getName(),
                "colour": colour,
                "index": position
            }
            self.appendItem(item)

        self.sort(lambda item: item["index"])
