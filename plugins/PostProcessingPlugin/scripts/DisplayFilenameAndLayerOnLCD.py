# Cura PostProcessingPlugin
# Author:   Amanda de Castilho
# Date:     August 28, 2018
# Modified: November 16, 2018 by Joshua Pope-Lewis

# Description:  This plugin is now an option in 'Display Info on LCD'

from ..Script import Script
from UM.Message import Message

class DisplayFilenameAndLayerOnLCD(Script):
    def initialize(self) -> None:
        Message(title = "[Display Filename and Layer on LCD]", text = "This script is now an option in 'Display Info on LCD'.  This post processor no longer works.").show()
    
    def getSettingDataString(self):
        return """{
            "name": "Display Filename And Layer On LCD",
            "key": "DisplayFilenameAndLayerOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_script":
                {
                    "label": "Deprecated/Obsolete",
                    "description": "This script is now included in 'Display Info on LCD'.",
                    "type": "bool",
                    "default_value": true
                }
            }
        }"""

    def execute(self, data):
        Message(title = "[Display Filename and Layer on LCD]", text = "This post is now included in 'Display Info on LCD'.  This script will exit.").show()
        data[0] += ";  [Display Filename and Layer on LCD]  Did not run.  It is now included in 'Display Info on LCD'.\n"
        return data
