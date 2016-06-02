# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt

import cura.ExtruderManager
import UM.Qt.ListModel

##  Model that holds extruders.
#
#   This model is designed for use by any list of extruders, but specifically
#   intended for drop-down lists of extruders in place of settings.
class ExtrudersModel(UM.Qt.ListModel.ListModel):
    ##  Human-readable name of the extruder.
    NameRole = Qt.UserRole + 1

    ##  Colour of the material loaded in the extruder.
    ColourRole = Qt.UserRole + 2

    ##  Index of the extruder, which is also the value of the setting itself.
    #
    #   An index of 0 indicates the first extruder, an index of 1 the second
    #   one, and so on. This is the value that will be saved in instance
    #   containers.
    IndexRole = Qt.UserRole + 3

    ##  Initialises the extruders model, defining the roles and listening for
    #   changes in the data.
    #
    #   \param parent Parent QtObject of this list.
    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ColourRole, "colour")
        self.addRoleName(self.IndexRole, "index")

        #Listen to changes.
        manager = cura.ExtruderManager.ExtruderManager.getInstance()
        manager.extrudersChanged.connect(self._updateExtruders())

    ##  Update the list of extruders.
    #
    #   This should be called whenever the list of extruders changes.
    def _updateExtruders(self):
        self.clear()
        manager = cura.ExtruderManager.ExtruderManager.getInstance()
        for index, extruder in enumerate(manager):
            item = { #Construct an item with only the relevant information.
                "name": extruder.name,
                "colour": extruder.material.getMetaDataEntry("color_code", default = "#FFFF00"),
                "index": index
            }
            self.appendItem(item)
        self.sort(lambda item: item["index"])