# Klipper Print stats (Script for PostProcessingPlugin)
########################################################################################################
# This script will pass slicer info (current layer and total layers) to klipper.
# See https://www.klipper3d.org/G-Codes.html?h=set_print_stats_info#set_print_stats_info
# It's also possible to add M117, M118 or custom commands including variables (see below).
# Possible variables are:
# ;current_layer;, ;z_height;, ;total_layers;, ;remaining_layers;, ;layer_height;, ;remaining_seconds;,
# ;elapsed_seconds;, ;total_seconds;, ;total_time;, ;total_time_formated;, ;elapsed_time;,
# ;elapsed_time_formated;, ;remaining_time;, ;remaining_time_formated;
#######################################################################################################
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms
# Author: Even Kraus (github.com/subdancer)

# History / change-log:
# - February 22, 2024
#       V1.0.0 - Initial Contribiution

from ..Script import Script
import time

class KlipperPrintStats(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Klipper Print Stats",
            "key": "KlipperPrintStats",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_print_stats":
                {
                    "label": "Enable Klipper Print Stats",
                    "description": "Adds necessary commands for the Klipper Print Stats ( Total Layers and Current Layer ) into the gcode file. See https://www.klipper3d.org/G-Codes.html?h=set_print_stats_info#set_print_stats_info",
                    "type": "bool",
                    "default_value": true
                },
                "warmup_time":
                {
                    "label": "Warmup Time (seconds)",
                    "description": "The time it takes for your printer from the moment you start the print till everything is on temperature and it actually starts the print. Every printer is different so this needs to be adjusted manually and corrected if print temperatures/material are changed. Please enter the time in seconds. This value is necessary to have acurate duration variables (;remainting_time; etc.). Ignore this if you don't use M117 or M118 Messages and time calculated variables.",
                    "type": "str",
                    "default_value": "180"
                },
                "enable_m117":
                {
                    "label": "Enable M117",
                    "description": "Enable a custom M117 Message at every layer change.",
                    "type": "bool",
                    "default_value": false
                },
                "message_m117":
                {
                    "label": "M117 Message",
                    "description": "Message that will be injected into a M117 command. Possible variables are ;current_layer;, ;z_height;, ;total_layers;, ;layer_height;, ;remaining_seconds;, ;elapsed_seconds;, ;total_seconds;, ;total_time;, ;total_time_formated;, ;elapsed_time;, ;elapsed_time_formated;, ;remaining_time; or ;remaining_time_formated;.",
                    "type": "str",
                    "default_value": "Printing layer ;current_layer;/;total_layers;, ;remaining_layers; left. Z-height: ;z_height; mm. Remaining time: ;remaining_time; + Elapsed time: ;elapsed_time;."
                },
                "enable_m118":
                {
                    "label": "Enable M118",
                    "description": "Enable a custom M118 Message at every layer change.",
                    "type": "bool",
                    "default_value": false
                },
                "message_m118":
                {
                    "label": "M118 Message",
                    "description": "Message that will be injected into a M118 command. Possible variables are ;current_layer;, ;z_height;, ;total_layers;, ;layer_height;, ;remaining_seconds;, ;elapsed_seconds;, ;total_seconds;, ;total_time;, ;total_time_formated;, ;elapsed_time;, ;elapsed_time_formated;, ;remaining_time; or ;remaining_time_formated;.",
                    "type": "str",
                    "default_value": "Printing layer ;current_layer;/;total_layers;, ;remaining_layers; left. Z-height: ;z_height; mm. Remaining time: ;remaining_time; + Elapsed time: ;elapsed_time;."
                },
                "enable_custom_gcode_line":
                {
                    "label": "Enable custom gcode line",
                    "description": "Enable a custom gcode line at every layer change.",
                    "type": "bool",
                    "default_value": false
                },
                "custom_gcode_line":
                {
                    "label": "Gcode line",
                    "description": "Custom Gcode line that will be injected before a layer change. Possible variables are ;current_layer;, ;z_height;, ;total_layers;, ;layer_height;, ;remaining_seconds;, ;elapsed_seconds;, ;total_seconds;, ;total_time;, ;total_time_formated;, ;elapsed_time;, ;elapsed_time_formated;, ;remaining_time; or ;remaining_time_formated;.",
                    "type": "str",
                    "default_value": ";Custom Line before the next layer"
                }
            }
        }"""

    def execute(self, data):
        print_stats_enabled = self.getSettingValueByKey("enable_print_stats")
        m117_enabled = self.getSettingValueByKey("enable_m117")
        m117_message = str(self.getSettingValueByKey("message_m117")) + "\n"
        m118_enabled = self.getSettingValueByKey("enable_m118")
        m118_message = str(self.getSettingValueByKey("message_m118")) + "\n"
        custom_gcode_enabled = self.getSettingValueByKey("enable_custom_gcode_line")
        custom_gcode = self.getSettingValueByKey("custom_gcode_line") + "\n"
        warmup_time = int(self.getSettingValueByKey("warmup_time"))
        layer_height = 0.0
        z_height = 0.0
        current_layer = 0
        total_layers = 0
        remaining_layers = 0
        total_seconds = 0.0
        elapsed_seconds = 0.0
        remaining_seconds = 0.0
        total_time_formated = ""
        total_time = ""
        elapsed_time_formated = ""
        elapsed_time = ""
        remaining_time_formated = ""
        remaining_time = ""

        if warmup_time is None:
            warmup_time = 0
        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                index = data.index(layer)
                if line.startswith(";Filament used:"):
                    layer = layer + ";Warmup time:" + str(warmup_time) + "\n"
                    data[index] = layer
                if line.startswith(";TIME:"):
                    total_seconds = float(line.split(":")[1]) + warmup_time
                    total_time_formated = time.strftime('%H hours, %M minutes and %S seconds', time.gmtime(total_seconds))
                    total_time = time.strftime('%H:%M:%S', time.gmtime(total_seconds))
                    elapsed_time_formated = time.strftime('%H hours, %M minutes and %S seconds', time.gmtime(elapsed_seconds + warmup_time))
                    elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_seconds + warmup_time))
                    remaining_seconds = total_seconds - elapsed_seconds - warmup_time
                    remaining_time_formated = time.strftime('%H hours, %M minutes and %S seconds', time.gmtime(remaining_seconds))
                    remaining_time = time.strftime('%H:%M:%S', time.gmtime(remaining_seconds))
                elif line.startswith(";Layer height:"):
                    layer_height = float(line.split(":")[1].replace(" ", ""))
                elif line.startswith(";TIME_ELAPSED:"):
                    elapsed_seconds = float(line.split(":")[1]) + warmup_time
                    elapsed_time_formated = time.strftime('%H hours, %M minutes and %S seconds', time.gmtime(elapsed_seconds))
                    elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_seconds))
                    remaining_seconds = total_seconds - elapsed_seconds
                    remaining_time_formated = time.strftime('%H hours, %M minutes and %S seconds', time.gmtime(remaining_seconds))
                    remaining_time = time.strftime('%H:%M:%S', time.gmtime(remaining_seconds))
                elif line.startswith(";LAYER_COUNT:"):
                    total_layers = int(line.split(":")[1])
                    if print_stats_enabled:
                        layer =  layer + "SET_PRINT_STATS_INFO TOTAL_LAYER=" + str(total_layers) + "\n"
                        data[index] = layer
                elif line.startswith(";LAYER:"):
                    current_layer = int(line.split(":")[1]) + 1
                    remaining_layers = total_layers - current_layer
                    z_height = float(current_layer) * float(layer_height)
                    z_height = format(z_height, '.2f')
                    if m118_enabled:
                        nM118_message = m118_message.replace(";current_layer;", str(current_layer)).replace(";z_height;", str(z_height)).replace(";total_layers;", str(total_layers)).replace(";layer_height;", str(layer_height)).replace(";remaining_layers;", str(remaining_layers)).replace(";remaining_seconds;", str(remaining_seconds)).replace(";elapsed_seconds;", str(elapsed_seconds)).replace(";total_seconds;", str(total_seconds)).replace(";total_time_formated;", str(total_time_formated)).replace(";elapsed_time_formated;", str(elapsed_time_formated)).replace(";remaining_time_formated;", str(remaining_time_formated)).replace(";total_time;", str(total_time)).replace(";elapsed_time;", str(elapsed_time)).replace(";remaining_time;", str(remaining_time))
                        layer = "M118 " + nM118_message + layer
                        data[index] = layer
                    if m117_enabled:
                        nM117_message = m117_message.replace(";current_layer;", str(current_layer)).replace(";z_height;", str(z_height)).replace(";total_layers;", str(total_layers)).replace(";layer_height;", str(layer_height)).replace(";remaining_layers;", str(remaining_layers)).replace(";remaining_seconds;", str(remaining_seconds)).replace(";elapsed_seconds;", str(elapsed_seconds)).replace(";total_seconds;", str(total_seconds)).replace(";total_time_formated;", str(total_time_formated)).replace(";elapsed_time_formated;", str(elapsed_time_formated)).replace(";remaining_time_formated;", str(remaining_time_formated)).replace(";total_time;", str(total_time)).replace(";elapsed_time;", str(elapsed_time)).replace(";remaining_time;", str(remaining_time))
                        layer = "M117 " + nM117_message + layer
                        data[index] = layer
                    if print_stats_enabled:
                        layer = "SET_PRINT_STATS_INFO CURRENT_LAYER=" + str(current_layer) + "\n" + layer
                        data[index] = layer
                    if custom_gcode_enabled:
                        layer = str(custom_gcode) + layer
                        data[index] = layer
        return data