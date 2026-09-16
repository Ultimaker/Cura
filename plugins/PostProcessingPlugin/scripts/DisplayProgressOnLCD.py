# Cura PostProcessingPlugin
# Author:   Mathias Lyngklip Kjeldgaard, Alexander Gee, Kimmo Toivanen, Inigo Martinez
# Date:     July 31, 2019
# Modified: Nov 30, 2021

# Description:  This plugin displays progress on the LCD. It can output the estimated time remaining and the completion percentage.

from ..Script import Script

from UM.Message import Message

class DisplayProgressOnLCD(Script):

    def initialize(self) -> None:
        Message(title = "[Display Progress on LCD]", text = "This script is now an option in 'Display Info on LCD'.  This post processor no longer works.").show()
        
    def getSettingDataString(self):
        return """{
            "name": "Display Progress On LCD",
            "key": "DisplayProgressOnLCD",
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
        Message(title = "[Display Progress on LCD]", text = "This post is now included in 'Display Info on LCD'.  This script will exit.").show()
        data[0] += ";  [Display Progress on LCD]  Did not run.  It is now included in 'Display Info on LCD'.\n"
        return data
