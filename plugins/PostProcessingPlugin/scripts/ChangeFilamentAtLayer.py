from ..Script import Script
from UM.Logger import Logger
from PyQt5.QtWidgets import QMessageBox

# Written 2018 by A.J.Bauer
#  - Tested with Cr-10 printer using stock firmware, gcode flavor in Cura set to "Marlin"
#  - M600 since Marlin 1.1.0, requires LCD display
#  - To debug, uncomment "Logger.." and check logs under windows: C:\Users\<USER>\AppData\Local\cura\stderr.log

class ChangeFilamentAtLayer(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Marlin Filament Change (M600)",
            "key": "ChangeFilamentAtLayer",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "change_at_layer":
                {
                    "label": "Change at Layer",
                    "description": "The number of the layer for filament change, the layer at which the new filament is to be used, matches the number in Layer View.",
                    "unit": "integer",
                    "type": "int",
                    "default_value": 2
                },
                "filament_change_x":
                {
                    "label": "Change pos X",
                    "description": "X position for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 50.0
                },
                "filament_change_y":
                {
                    "label": "Change pos Y",
                    "description": "Y position for filament change.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 50.0
                },
                "filament_change_relative_z":
                {
                    "label": "Change pos relative Z",
                    "description": "Z relative lift for filament change position.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 30.0
                }
            }
        }"""

    def execute(self, data: list):
        #Logger.log("i", "ChangeFilamentAtLayer post processing..")

        change_at_layer = self.getSettingValueByKey("change_at_layer")
        filament_change_x = self.getSettingValueByKey("filament_change_x")
        filament_change_y = self.getSettingValueByKey("filament_change_y")
        filament_change_relative_z = self.getSettingValueByKey("filament_change_relative_z")
        
        className = str(self.__class__.__name__)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(className + " has a problem")

        layerHeightNormal = 0;
        lines = data[0].splitlines()
        for i in range(len(lines)):
            if ";Layer height:" in lines[i]:
                layerHeightNormal = float(lines[i].split(":")[1]);
                #Logger.log("d", "layerHeightNormal: " + str(layerHeightNormal))
        if layerHeightNormal == 0:
            msg.setInformativeText("Layer height not found in gcode! Nothing changed in gcode.")
            retval = msg.exec_()
            return data

        layerToChangeFound = False;
        layerHeightFirst = 0.0        
        layerCountFound = False
        layerNumber = 0      

        for l in range(len(data)):
            lines = data[l].splitlines()
            for i in range(len(lines)):
                if "LAYER_COUNT" in lines[i]:                    
                    layerCountFound = True
                
                if layerCountFound and (self.getValue(lines[i], 'G') == 1 or self.getValue(lines[i], 'G')) == 0:
                    z = self.getValue(lines[i], 'Z')
                    if z is not None:
                        if layerHeightFirst == 0.0:
                            layerHeightFirst = z
                            layerNumber = 1
                            #Logger.log("d", "layerHeightFirst: " + str(layerHeightFirst))
                        else:
                            layerNumber = int(round(float(z - layerHeightFirst) / layerHeightNormal, 0)) + 1

                        #Logger.log("d", "layerNumber: " + str(layerNumber) + ", z (after layer): " + str(z))                        

                        if layerNumber == change_at_layer:
                            gcodeM600 = ";" + className + "\n" + "M600 X" + str(round(filament_change_x, 2)) + " Y" + str(round(filament_change_y, 2)) + " Z" + str(round(filament_change_relative_z, 2)) + "\n"
                            data[l] = "M113 60" + "\n" + gcodeM600 + data[l]
                            layerToChangeFound = True

        if not layerToChangeFound:
            if not layerCountFound:
                msg.setInformativeText("Could not find LAYERCOUNT in gcode!")
            else:
                msg.setInformativeText("Could not find the layer for filament change!")

            retval = msg.exec_()
        return data
