# Copyright (c) 2023 GregValiant (Greg Foresi)
#   This PostProcessingPlugin is released under the terms of the AGPLv3 or higher.
#   This post-processor opens the "Post Processor ReadMe.pdf file in the system viewer.

from UM.Platform import Platform
from ..Script import Script
from UM.Application import Application
import os

class AAA_PostProcessReadMe(Script):

    def __init__(self):
        super().__init__()

    def initialize(self) -> None:
        super().initialize()
        
        SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
        if Platform.isWindows:        
            text_file = os.startfile(SCRIPT_DIR + "\Post Processor ReadMe.pdf")
        elif Platform.isOSX():
            text_file = open(SCRIPT_DIR + "\Post Processor ReadMe.pdf")
        elif Platform.isLinux:
            text_file = os.system(SCRIPT_DIR + "\Post Processor ReadMe.pdf")
            
    def getSettingDataString(self):
        return """{
            "name": "Help (PDF file)",
            "key": "AAA_PostProcessReadMe",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "auto_open":
                {
                    "label": "Auto-Open Descriptions",
                    "description": "",
                    "type": "bool",
                    "value": true,
                    "enabled": false
                }
            }
        }"""
           
