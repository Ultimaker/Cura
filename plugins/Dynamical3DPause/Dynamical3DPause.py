# Copyright (c) 2017 Ultimaker B.V.
# This example is released under the terms of the AGPLv3 or higher.

import os.path
import re
from plugins.PostProcessingPlugin.Script import Script
from typing import List, Any
from PyQt5.QtCore import pyqtProperty, pyqtSignal, Qt, QUrl, QObject, QVariant #To define a shortcut key and to find the QML files, and to expose information to QML.
from PyQt5.QtQml import QQmlComponent, QQmlContext #To create a dialogue window.

from UM.Application import Application #To register the information dialogue.
from UM.Event import Event #To understand what events to react to.
from UM.PluginRegistry import PluginRegistry #To find the QML files in the plug-in folder.
from UM.Scene.Selection import Selection #To get the current selection and some information about it.
from UM.Tool import Tool #The PluginObject we're going to extend.
from UM.Application import Application
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication

class Dynamical3DPause(Tool): #The Tool class extends from PluginObject, and we have to be a PluginObject for the plug-in to load.
    ##  Creates an instance of this tool.
    #
    #   Here you can set some additional metadata.
    def __init__(self):
        super().__init__()

        ##self._shortcut_key = Qt.Key_X

        #This plug-in creates a window with information about the objects we've selected. That window is lazily-loaded.
        self.info_window = None
        self._script_list = []  # type: List[Script]
        self.points = [5]
        ## Reacting to an event. ##
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self.execute)

    def prueba(self, output_device) -> None:
        if self.info_window is None:
            self.info_window = self._createDialogue()
        self.info_window.show()

    ##  Called when something happens in the scene while our tool is active.
    #
    #   For instance, we can react to mouse clicks, mouse movements, and so on.
    def event(self, event):
        super().event(event) #The super event updates the selection if the user clicks on some object.

        if event.type == Event.MouseReleaseEvent and Selection.hasSelection(): #Only if something is selected.
            #As example for this tool, we'll spawn a message with some information.
            if self.info_window is None:
                self.info_window = self._createDialogue()
            self.info_window.show()

    ##  Creates a modal dialogue with information about the selection.
    def _createDialogue(self):
        #Create a QML component from the SelectionInfo.qml file.
        qml_file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "SelectionInfo.qml")
        component = Application.getInstance().createQmlComponent(qml_file_path)

        return component

    def execute(self, output_device) -> None:
        """Execute all post-processing scripts on the gcode."""

        scene = Application.getInstance().getController().getScene()
        # If the scene does not have a gcode, do nothing
        if not hasattr(scene, "gcode_dict"):
            return
        gcode_dict = getattr(scene, "gcode_dict")
        if not gcode_dict:
            return

        # get gcode list for the active build plate
        active_build_plate_id = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        gcode_list = gcode_dict[active_build_plate_id]
        if not gcode_list:
            return

        if ";POSTPROCESSED" not in gcode_list[0]:
            for point in self.points:
                try:
                    gcode_list =  self.executeScript(point,gcode_list)
                except Exception:
                    Logger.logException("e", "Exception in post-processing script.")
            if len(self.points):  # Add comment to g-code if any changes were made.
                gcode_list[0] += ";POSTPROCESSED\n"
            gcode_dict[active_build_plate_id] = gcode_list
            setattr(scene, "gcode_dict", gcode_dict)
        else:
            Logger.log("e", "Already post processed")

    def executeScript(self, point, data: list):

        """data is a list. Each index contains a layer"""

        current_z = 0.
        layers_started = False
       

        # use offset to calculate the current height: <current_height> = <current_z> - <layer_0_z>
        layer_0_z = 0.
        got_first_g_cmd_on_layer_0 = False
        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:0" in line:
                    layers_started = True
                    continue

                if not layers_started:
                    continue

                if (self.getValue(line, 'G') == 1 or self.getValue(line, 'G') == 0) and 'X' in line and 'Y' in line and 'Z' in line:
                    current_z = self.getValue(line, 'Z')
                    if not got_first_g_cmd_on_layer_0:
                        layer_0_z = current_z
                        got_first_g_cmd_on_layer_0 = True

                    if current_z is not None:
                        current_height = current_z - layer_0_z
                        if current_height >= point:
                            index = data.index(layer)

                            prepend_gcode = ";TYPE:CUSTOM\n"
                            prepend_gcode += ";added code by plugin Dynamical3D Pause\n"
                            prepend_gcode += ";current z: %f \n" % current_z
                            prepend_gcode += ";current height: %f \n" % current_height
                            prepend_gcode += "M0 ;stop\n"
                            layer = prepend_gcode + layer

                            # Override the data of this layer with the
                            # modified data
                            data[index] = layer
                            return data
                        break
        return data

    def getValue(self, line: str, key: str, default = None) -> Any:
        """Convenience function that finds the value in a line of g-code.

        When requesting key = x from line "G1 X100" the value 100 is returned.
        """
        if not key in line or (';' in line and line.find(key) > line.find(';')):
            return default
        sub_part = line[line.find(key) + 1:]
        m = re.search('^-?[0-9]+\.?[0-9]*', sub_part)
        if m is None:
            return default
        try:
            return int(m.group(0))
        except ValueError: #Not an integer.
            try:
                return float(m.group(0))
            except ValueError: #Not a number at all.
                return default