# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSignal, pyqtProperty

import UM.Qt.ListModel

from . import ExtruderManager

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
    ColorRole = Qt.UserRole + 3

    ##  Index of the extruder, which is also the value of the setting itself.
    #
    #   An index of 0 indicates the first extruder, an index of 1 the second
    #   one, and so on. This is the value that will be saved in instance
    #   containers.
    IndexRole = Qt.UserRole + 4

    ##  List of colours to display if there is no material or the material has no known
    #   colour.
    defaultColors = ["#ffc924", "#86ec21", "#22eeee", "#245bff", "#9124ff", "#ff24c8"]

    ##  Initialises the extruders model, defining the roles and listening for
    #   changes in the data.
    #
    #   \param parent Parent QtObject of this list.
    def __init__(self, parent = None):
        super().__init__(parent)

        self.addRoleName(self.IdRole, "id")
        self.addRoleName(self.NameRole, "name")
        self.addRoleName(self.ColorRole, "color")
        self.addRoleName(self.IndexRole, "index")

        self._add_global = False

        self._active_extruder_stack = None

        #Listen to changes.
        manager = ExtruderManager.getInstance()
        manager.extrudersChanged.connect(self._updateExtruders) #When the list of extruders changes in general.

        self._updateExtruders()

        manager.activeExtruderChanged.connect(self._onActiveExtruderChanged)
        self._onActiveExtruderChanged()

    def setAddGlobal(self, add):
        if add != self._add_global:
            self._add_global = add
            self._updateExtruders()
            self.addGlobalChanged.emit()

    addGlobalChanged = pyqtSignal()

    @pyqtProperty(bool, fset = setAddGlobal, notify = addGlobalChanged)
    def addGlobal(self):
        return self._add_global

    def _onActiveExtruderChanged(self):
        manager = ExtruderManager.getInstance()
        active_extruder_stack = manager.getActiveExtruderStack()
        if self._active_extruder_stack != active_extruder_stack:
            if self._active_extruder_stack:
                self._active_extruder_stack.containersChanged.disconnect(self._onExtruderStackContainersChanged)

            if active_extruder_stack:
                # Update the model when the material container is changed
                active_extruder_stack.containersChanged.connect(self._onExtruderStackContainersChanged)
            self._active_extruder_stack = active_extruder_stack


    def _onExtruderStackContainersChanged(self, container):
        # The ExtrudersModel needs to be updated when the material-name or -color changes, because the user identifies extruders by material-name
        if container.getMetaDataEntry("type") == "material":
            self._updateExtruders()

    modelChanged = pyqtSignal()

    ##  Update the list of extruders.
    #
    #   This should be called whenever the list of extruders changes.
    def _updateExtruders(self):
        changed = False

        if self.rowCount() != 0:
            changed = True

        items = []

        global_container_stack = UM.Application.getInstance().getGlobalContainerStack()
        if global_container_stack:
            if self._add_global:
                material = global_container_stack.findContainer({ "type": "material" })
                color = material.getMetaDataEntry("color_code", default = self.defaultColors[0]) if material else self.defaultColors[0]
                item = {
                    "id": global_container_stack.getId(),
                    "name": "Global",
                    "color": color,
                    "index": -1
                }
                items.append(item)
                changed = True

            manager = ExtruderManager.getInstance()
            for extruder in manager.getMachineExtruders(global_container_stack.getId()):
                extruder_name = extruder.getName()
                material = extruder.findContainer({ "type": "material" })
                if material:
                    extruder_name = "%s (%s)" % (material.getName(), extruder_name)
                position = extruder.getMetaDataEntry("position", default = "0")  # Get the position
                try:
                    position = int(position)
                except ValueError: #Not a proper int.
                    position = -1
                default_color = self.defaultColors[position] if position >= 0 and position < len(self.defaultColors) else self.defaultColors[0]
                color = material.getMetaDataEntry("color_code", default = default_color) if material else default_color
                item = { #Construct an item with only the relevant information.
                    "id": extruder.getId(),
                    "name": extruder_name,
                    "color": color,
                    "index": position
                }
                items.append(item)
                changed = True

        if changed:
            items.sort(key = lambda i: i["index"])
            self.setItems(items)
            self.modelChanged.emit()
