# ChangeAtZ script - Change printing parameters at a given height
# This script is the successor of the TweakAtZ plugin for legacy Cura.
# It contains code from the TweakAtZ plugin V1.0-V4.x and from the ExampleScript by Jaime van Kessel, Ultimaker B.V.
# It runs with the PostProcessingPlugin which is released under the terms of the LGPLv3 or higher.
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

# Authors of the ChangeAtZ plugin / script:
# Written by Steven Morlock, smorloc@gmail.com
# Modified by Ricardo Gomez, ricardoga@otulook.com, to add Bed Temperature and make it work with Cura_13.06.04+
# Modified by Stefan Heule, Dim3nsioneer@gmx.ch since V3.0 (see changelog below)
# Modified by Jaime van Kessel (Ultimaker), j.vankessel@ultimaker.com to make it work for 15.10 / 2.x
# Modified by Ghostkeeper (Ultimaker), rubend@tutanota.com, to debug.
# Modified by Wes Hanney, https://github.com/novamxd, Retract Length + Speed, Clean up
# Modified by Alex Jaxon, https://github.com/legend069, Added option to modify Build Volume Temperature


# history / changelog:
# V3.0.1:   TweakAtZ-state default 1 (i.e. the plugin works without any TweakAtZ comment)
# V3.1:     Recognizes UltiGCode and deactivates value reset, fan speed added, alternatively layer no. to tweak at,
# extruder three temperature disabled by "#Ex3"
# V3.1.1:   Bugfix reset flow rate
# V3.1.2:   Bugfix disable TweakAtZ on Cool Head Lift
# V3.2:     Flow rate for specific extruder added (only for 2 extruders), bugfix parser,
# added speed reset at the end of the print
# V4.0:     Progress bar, tweaking over multiple layers, M605&M606 implemented, reset after one layer option,
# extruder three code removed, tweaking print speed, save call of Publisher class,
# uses previous value from other plugins also on UltiGCode
# V4.0.1:	Bugfix for doubled G1 commands
# V4.0.2:	Uses Cura progress bar instead of its own
# V4.0.3:	Bugfix for cool head lift (contributed by luisonoff)
# V4.9.91:	First version for Cura 15.06.x and PostProcessingPlugin
# V4.9.92:	Modifications for Cura 15.10
# V4.9.93:	Minor bugfixes (input settings) / documentation
# V4.9.94:	Bugfix Combobox-selection; remove logger
# V5.0:		Bugfix for fall back after one layer and doubled G0 commands when using print speed tweak, Initial version for Cura 2.x
# V5.0.1:	Bugfix for calling unknown property 'bedTemp' of previous settings storage and unknown variable 'speed'
# V5.1:		API Changes included for use with Cura 2.2
# V5.2.0:	Wes Hanney. Added support for changing Retract Length and Speed. Removed layer spread option. Fixed issue of cumulative ChangeAtZ
# mods so they can now properly be stacked on top of each other. Applied code refactoring to clean up various coding styles. Added comments.
# Broke up functions for clarity. Split up class so it can be debugged outside of Cura.
# V5.2.1:	Wes Hanney. Added support for firmware based retractions. Fixed issue of properly restoring previous values in single layer option.
# Added support for outputting changes to LCD (untested). Added type hints to most functions and variables. Added more comments. Created GCodeCommand
# class for better detection of G1 vs G10 or G11 commands, and accessing arguments. Moved most GCode methods to GCodeCommand class. Improved wording
# of Single Layer vs Keep Layer to better reflect what was happening.
# V5.3.0    Alex Jaxon, Added option to modify Build Volume Temperature keeping current format
# V5.4.0    Wes Hanney. Fixed issues #8574 and #8886 where the script would not properly apply (or change back) certain values. Z targeting now works by determining the target layer based on the minimum Z for a given layer. Added support for layer and Z ranges. Added support for reading layer height from project settings. 


# Uses -
# M220 S<factor in percent> - set speed factor override percentage
# M221 S<factor in percent> - set flow factor override percentage
# M221 S<factor in percent> T<0-#toolheads> - set flow factor override percentage for single extruder
# M104 S<temp> T<0-#toolheads> - set extruder <T> to target temperature <S>
# M140 S<temp> - set bed target temperature
# M106 S<PWM> - set fan speed to target speed <S>
# M207 S<mm> F<mm/m> - set the retract length <S> or feed rate <F>
# M117 - output the current changes

from ..Script import Script
from math import floor
from tempfile import mkdtemp
from UM.Application import Application
from UM.Logger import Logger
import copy
import json
import os.path
import re

temp_dir = mkdtemp("", "ChangeAtZ")
os.makedirs(temp_dir, exist_ok=True)

Logger.info("ChangeAtZ dir: %s", temp_dir)

executions = 0


# this was broken up into a separate class so the main ChangeAtZ script could be debugged outside of Cura
class ChangeAtZ(Script):
    version = "5.4.0"

    def getSettingDataString(self):
        return """{
            "name": "ChangeAtZ """ + self.version + """ (Experimental)",
            "key": "ChangeAtZ",
            "metadata": {},
            "version": 2,
            "settings": {
                "caz_enabled": {
                    "label": "Enabled",
                    "description": "Allows adding multiple ChangeAtZ mods and disabling them as needed.",
                    "type": "bool",
                    "default_value": true
                },
                "a_trigger": {
                    "label": "Trigger",
                    "description": "Trigger at height or at layer no.",
                    "type": "enum",
                    "options": {
                        "height": "Height",
                        "layer_no": "Layer No."
                    },
                    "default_value": "height"
                },
                "b_targetZ": {
                    "label": "Start Height (mm)",
                    "description": "The Z height to start apply the changes to",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0.1",
                    "maximum_value_warning": "230",
                    "enabled": "a_trigger == 'height'"
                },
                "b_targetZEnd": {
                    "label": "End Height (mm)",
                    "description": "Optional. The modifications will go up to and include this Z height",
                    "unit": "mm",
                    "type": "float",
                    "default_value": -1.0,
                    "minimum_value": "-1.0",               
                    "enabled": "a_trigger == 'height'"
                },
                "b_targetL": {
                    "label": "Start Layer (#)",
                    "description": "The layer number, starting at 0, to apply the changes to",
                    "unit": "#",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "-100",
                    "minimum_value_warning": "-1",
                    "enabled": "a_trigger == 'layer_no'"
                },
                "b_targetLEnd": {
                    "label": "End Layer (#)",
                    "description": "Optional. The modifications will go up to and include this layer number",
                    "unit": "#",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": "-1",                   
                    "enabled": "a_trigger == 'layer_no'"
                },
                "c_behavior": {
                    "label": "Apply To",
                    "description": "Target Layer + Subsequent Layers is good for testing changes between ranges of layers, ex: Layer 0 to 10 or 0mm to 5mm. Single layer is good for testing changes at a single layer, ex: at Layer 10 or 5mm only.",
                    "type": "enum",
                    "options": {
                        "keep_value": "Target Layer + Subsequent Layers",
                        "single_layer": "Target Layer Only"
                    },
                    "default_value": "keep_value"
                },
                "caz_output_to_display": {
                    "label": "Output to Display",
                    "description": "Displays the current changes to the LCD",
                    "type": "bool",
                    "default_value": false
                },
                "e1_Change_speed": {
                    "label": "Change Global Speed",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "e2_speed": {
                    "label": "Global Speed (%)",
                    "description": "Sets the M220 value",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": "e1_Change_speed"
                },
                "f1_Change_printspeed": {
                    "label": "Change Print Speed",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "f2_printspeed": {
                    "label": "Print Speed (%)",
                    "description": "Alters the feed rate (F) on all the G0 and G1 commands",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": "f1_Change_printspeed"
                },
                "g1_Change_flowrate": {
                    "label": "Change Flow Rate",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "g2_flowrate": {
                    "label": "Flow Rate (%)",
                    "description": "Sets the M221 global value",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": "g1_Change_flowrate"
                },
                "g3_Change_flowrateOne": {
                    "label": "Change Flow Rate 1",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "g4_flowrateOne": {
                    "label": "Flow Rate 1 (%)",
                    "description": "Sets the M221 T0 value",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": "g3_Change_flowrateOne"
                },
                "g5_Change_flowrateTwo": {
                    "label": "Change Flow Rate 2",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "g6_flowrateTwo": {
                    "label": "Flow Rate 2 (%)",
                    "description": "Sets the M221 T1 value",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "1",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "200",
                    "enabled": "g5_Change_flowrateTwo"
                },
                "h1_Change_bedTemp": {
                    "label": "Change Bed Temp",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "h2_bedTemp": {
                    "label": "Bed Temp (ºC)",
                    "description": "Sets the M140 value",
                    "unit": "ºC",
                    "type": "float",
                    "default_value": 60,
                    "minimum_value": "0",
                    "minimum_value_warning": "30",
                    "maximum_value_warning": "120",
                    "enabled": "h1_Change_bedTemp"
                },
                "h1_Change_buildVolumeTemperature": {
                    "label": "Change Build Volume Temperature",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "h2_buildVolumeTemperature": {
                    "label": "Build Volume Temperature (ºC)",
                    "description": "Sets the M141 value",
                    "unit": "ºC",
                    "type": "float",
                    "default_value": 20,
                    "minimum_value": "0",
                    "minimum_value_warning": "10",
                    "maximum_value_warning": "50",
                    "enabled": "h1_Change_buildVolumeTemperature"
                },
                "i1_Change_extruderOne": {
                    "label": "Change Extruder 1 Temp",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "i2_extruderOne": {
                    "label": "Extruder 1 Temp (ºC)",
                    "description": "Sets the M104 T0 value",
                    "unit": "ºC",
                    "type": "float",
                    "default_value": 190,
                    "minimum_value": "0",
                    "minimum_value_warning": "160",
                    "maximum_value_warning": "250",
                    "enabled": "i1_Change_extruderOne"
                },
                "i3_Change_extruderTwo": {
                    "label": "Change Extruder 2 Temp",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "i4_extruderTwo": {
                    "label": "Extruder 2 Temp (ºC)",
                    "description": "Sets the M104 T1 value",
                    "unit": "ºC",
                    "type": "float",
                    "default_value": 190,
                    "minimum_value": "0",
                    "minimum_value_warning": "160",
                    "maximum_value_warning": "250",
                    "enabled": "i3_Change_extruderTwo"
                },
                "j1_Change_fanSpeed": {
                    "label": "Change Fan Speed",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false
                },
                "j2_fanSpeed": {
                    "label": "Fan Speed (%)",
                    "description": "Sets the M106 value",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "j1_Change_fanSpeed"
                },
                "caz_change_retract": {
                    "label": "Change Retraction",
                    "description": "Use to enable/disable this setting without clearing it. Does not work when using relative extrusion.",
                    "type": "bool",
                    "default_value": false
                },
                "caz_retractstyle": {
                    "label": "Retract Style",
                    "description": "Specify if you're using firmware retraction (G10/G11) or linear move (G0/G1) based retractions. Check your printer settings to see which you're using.",
                    "type": "enum",
                    "options": {
                        "linear": "Linear Move",
                        "firmware": "Firmware"
                    },
                    "default_value": "linear",
                    "enabled": "false"
                },
                "caz_change_retractfeedrate": {
                    "label": "Change Retract Feed Rate",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "caz_change_retract"
                },
                "caz_retractfeedrate": {
                    "label": "Retract Feed Rate (mm/s)",
                    "description": "Changes either the M207 (F) value -or- the G01/G02 feed rate (F) value",
                    "unit": "mm/s",
                    "type": "float",
                    "default_value": 40,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "100",
                    "enabled": "caz_change_retractfeedrate"
                },
                "caz_change_retractlength": {
                    "label": "Change Retract Length",
                    "description": "Use to enable/disable this setting without clearing it",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "caz_change_retract"
                },
                "caz_retractlength": {
                    "label": "Retract Length (mm)",
                    "description": "Changes either the M207 (S) value -or- the G01/G02 feed rate (E) value",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 6,
                    "minimum_value": "0",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "20",
                    "enabled": "caz_change_retractlength"
                }      
            }
        }"""

    def __init__(self):
        super().__init__()

    def execute(self, data: list[str]):

        caz_instance = ChangeAtZProcessor()

        caz_instance.targetValues = {}
        
        global_stack = Application.getInstance().getGlobalContainerStack()

        # copy over our settings to our change z class
        self.setIntSettingIfEnabled(caz_instance, "e1_Change_speed", "speed", "e2_speed")
        self.setIntSettingIfEnabled(caz_instance, "f1_Change_printspeed", "printspeed", "f2_printspeed")
        self.setIntSettingIfEnabled(caz_instance, "g1_Change_flowrate", "flowrate", "g2_flowrate")
        self.setIntSettingIfEnabled(caz_instance, "g3_Change_flowrateOne", "flowrateOne", "g4_flowrateOne")
        self.setIntSettingIfEnabled(caz_instance, "g5_Change_flowrateTwo", "flowrateTwo", "g6_flowrateTwo")
        self.setFloatSettingIfEnabled(caz_instance, "h1_Change_bedTemp", "bedTemp", "h2_bedTemp")
        self.setFloatSettingIfEnabled(caz_instance, "h1_Change_buildVolumeTemperature", "buildVolumeTemperature",
                                      "h2_buildVolumeTemperature")
        self.setFloatSettingIfEnabled(caz_instance, "i1_Change_extruderOne", "extruderOne", "i2_extruderOne")
        self.setFloatSettingIfEnabled(caz_instance, "i3_Change_extruderTwo", "extruderTwo", "i4_extruderTwo")
        self.setIntSettingIfEnabled(caz_instance, "j1_Change_fanSpeed", "fanSpeed", "j2_fanSpeed")
        self.setFloatSettingIfEnabled(caz_instance, "caz_change_retractfeedrate", "retractfeedrate",
                                      "caz_retractfeedrate")
        self.setFloatSettingIfEnabled(caz_instance, "caz_change_retractlength", "retractlength", "caz_retractlength")

        # is this mod enabled?
        caz_instance.enabled = self.getSettingValueByKey("caz_enabled")

        # are we emitting data to the LCD?
        caz_instance.displayChangesToLcd = self.getSettingValueByKey("caz_output_to_display")

        # are we doing linear move retractions?
        caz_instance.linearRetraction = bool(global_stack.getProperty("machine_firmware_retract", "value")) == False
        
        # see if we're applying to a single layer or to all layers hence forth
        caz_instance.applyToSingleLayer = self.getSettingValueByKey("c_behavior") == "single_layer"

        # used for easy reference of layer or height targeting
        caz_instance.targetByLayer = self.getSettingValueByKey("a_trigger") == "layer_no"

        # change our target based on what we're targeting
        caz_instance.targetLayerStart = self.getIntSettingByKey("b_targetL", None)
        caz_instance.targetLayerEnd = self.getFloatSettingByKey("b_targetLEnd", -1)
        caz_instance.targetZStart = self.getFloatSettingByKey("b_targetZ", None)
        caz_instance.targetZEnd = self.getFloatSettingByKey("b_targetZEnd", -1)
        caz_instance.layerHeight = float(global_stack.getProperty("layer_height", "value"))

        # run our script
        return caz_instance.execute(data)

    # Sets the given TargetValue in the ChangeAtZ instance if the trigger is specified
    def setIntSettingIfEnabled(self, caz_instance, trigger, target, setting):

        # stop here if our trigger isn't enabled
        if not self.getSettingValueByKey(trigger):
            return

        # get our value from the settings
        value = self.getIntSettingByKey(setting, None)

        # skip if there's no value or we can't interpret it
        if value is None:
            return

        # set our value in the target settings
        caz_instance.targetValues[target] = value

    # Sets the given TargetValue in the ChangeAtZ instance if the trigger is specified
    def setFloatSettingIfEnabled(self, caz_instance, trigger, target, setting):

        # stop here if our trigger isn't enabled
        if not self.getSettingValueByKey(trigger):
            return

        # get our value from the settings
        value = self.getFloatSettingByKey(setting, None)

        # skip if there's no value or we can't interpret it
        if value is None:
            return

        # set our value in the target settings
        caz_instance.targetValues[target] = value

    # Returns the given settings value as an integer or the default if it cannot parse it
    def getIntSettingByKey(self, key, default: int | None) -> int | None:

        # change our target based on what we're targeting
        try:
            return int(self.getSettingValueByKey(key))
        except:
            return default

    # Returns the given settings value as an integer or the default if it cannot parse it
    def getFloatSettingByKey(self, key, default: float | None) -> float | None:

        # change our target based on what we're targeting
        try:
            return float(self.getSettingValueByKey(key))
        except:
            return default


class GCodeCommand:
    # The GCode command itself (ex: G10)
    command: str | None = None

    # Anything that comes after the first semicolon in the command
    comment: str | None = None

    # Contains any arguments passed to the command. The key is the argument name, the value is the value of the argument.
    __arguments: dict[str, any] = {}

    # Contains the components of the command broken into pieces
    __components: list[str] = []

    # contains the order in which the arguments appear, this is primarily used for rendering back as a string
    __arguments_order: list[str] = []

    def __init__(self):
        """
        This class is used to understand and manipulate GCode commands programmatically. We lazy load the arguments because there are generally a lot of commands in a gcode file and we're normally only interested in a slice of them. If we limit it to identifying the command but then lazy load the arguments this saves a lot of processing time.
        """
        self.reset()

    def __eq__(self, other):
        if not type(other) is type(self):
            return False

        # if we don't do this they may still be the same command but we'd never know
        self.parseArguments()
        other.parseArguments()

        return (self.command == other.command
                and self.__arguments == other.__arguments
                and self.__components == other.__components)

    def __str__(self):
        pieces = [self.command]

        for arg in self.__arguments_order:
            value = self.getArgument(arg, "")

            pieces.append(arg + str(value))

        return " ".join(pieces) + (";" + self.comment if self.hasComment() else "")

    def asLinearMove(self):
        """
        Converts the command to a linear move command if it is one. If it is none a linear command it returns
        None.
        """
        if not self.isLinearMove():
            return None

        # convert our values to floats (or defaults)
        self.__arguments["F"] = self.getArgumentAsFloat("F")
        self.__arguments["X"] = self.getArgumentAsFloat("X")
        self.__arguments["Y"] = self.getArgumentAsFloat("Y")
        self.__arguments["Z"] = self.getArgumentAsFloat("Z")
        self.__arguments["E"] = self.getArgumentAsFloat("E")

        return self

    # Gets a GCode Command from the given single line of GCode
    @staticmethod
    def getFromLine(line: str):

        # obviously if we don't have a command, we can't return anything
        if line is None or len(line) == 0:
            return None

        # we only support G or M commands
        if line[0] != "G" and line[0] != "M":
            return None

        line = line.strip()
        comment_index = line.find(";")
        comment = None
        command = line

        if comment_index > 0:
            command = line[:comment_index].strip()
            comment = line[comment_index:].strip()

        # break into the individual components
        command_pieces = command.split(" ")

        # our return command details
        command = GCodeCommand()

        # stop here if we don't even have something to interpret
        if len(command_pieces) == 0:
            return None

        # stores all the components of the command within the class for later
        command.__components = command_pieces

        # set the actual command
        command.command = command_pieces[0]
        command.comment = comment

        # return our indexed command
        return command

    # Handy function for reading a linear move command
    @staticmethod
    def getLinearMoveCommand(line: str):

        # get our command from the line
        command = GCodeCommand.getFromLine(line)

        if command is None:
            return None

        return command.asLinearMove()

    # Gets the value of a parameter or returns the default if there is none
    def getArgument(self, name: str, default: any = None) -> any:

        # parse our arguments (only happens once)
        self.parseArguments()

        # if we don't have the parameter, return the default
        if name not in self.__arguments:
            return default

        # otherwise return the value
        return self.__arguments[name]

    # Gets the value of a parameter as a float or returns the default
    def getArgumentAsFloat(self, name: str, default: float = None) -> float | None:

        # try to parse as a float, otherwise return the default
        try:
            value = self.getArgument(name, default)

            if value is None:
                return default

            return float(value)
        except:
            return default

    # Gets the value of a parameter as an integer or returns the default
    def getArgumentAsInt(self, name: str, default: int = None) -> int | None:

        # try to parse as a integer, otherwise return the default
        try:
            value = self.getArgument(name, default)

            if value is None:
                return default

            return int(value)
        except:
            return default

    @staticmethod
    def getCommentArgument(line: str, key: str, default: str = None) -> str | None:
        """
        Some values can be stored directly as comments. This will retrieve it from the line
        """
        if key not in line:
            return default

        # allows for string lengths larger than 1
        sub_part = line[line.find(key) + len(key):]

        if sub_part is None:
            return default

        return sub_part.strip()

    @staticmethod
    def getCommentArgumentAsFloat(line: str, key: str, default: float = None) -> float | None:

        # get the value from the command
        value = GCodeCommand.getCommentArgument(line, key, default)

        # stop here if it's the default
        if value is None:
            return default

        try:
            return float(value)
        except:
            return default

    @staticmethod
    def getCommentArgumentAsInt(line: str, key: str, default: int = None) -> int | None:

        # get the value from the command
        value = GCodeCommand.getCommentArgument(line, key, default)

        # stop here if it's the default
        if value is None:
            return default

        try:
            return int(value)
        except:
            return default

    def hasArgument(self, key: str) -> bool:
        self.parseArguments()
        return key in self.__arguments

    def hasComment(self) -> bool:
        return not self.comment is None and len(self.comment) > 0

    def hasExtrudeAndFeed(self):
        self.parseArguments()
        return self.hasArgument("E") and self.hasArgument("F")

    def hasXYZ(self):
        self.parseArguments()
        return self.hasArgument("X") and self.hasArgument("Y") and self.hasArgument("Z")

    def isLinearMove(self) -> bool:
        return self.command == "G0" or self.command == "G1"

    def isRetraction(self):
        return not self.hasXYZ() and self.hasExtrudeAndFeed()

    # Parses the arguments of the command on demand, only once
    def parseArguments(self):
        # stop here if we don't have any remaining components
        if len(self.__components) <= 1:
            return None

        self.__arguments = {}
        self.__arguments_order = []

        # iterate and index all of our parameters, skip the first component as it's the command
        for i in range(1, len(self.__components)):

            # get our component
            component = self.__components[i]

            # get the first character of the parameter, which is the name
            component_name = component[0]

            # track the order in which they appear
            self.__arguments_order.append(component_name)

            # get the value of the parameter (the rest of the string
            component_value = None

            # get our value if we have one
            if len(component) > 1:
                component_value = component[1:]

            # index the argument
            self.__arguments[component_name] = component_value

        # clear the components to we don't process again
        self.__components = []

    # Resets the model back to defaults
    def reset(self):
        self.command = None
        self.__arguments = {}
        self.__arguments_order = []

    def setArgument(self, key: str, value: any):

        if value is None:
            self.__arguments.pop(key, None)
            return

        self.__arguments[key] = value


# The primary ChangeAtZ class that does all the gcode editing. This was broken out into an
# independent class so it could be debugged using a standard IDE
class ChangeAtZProcessor:
    # Holds our current height
    currentZ = 0

    # Holds the minimum height for the current layer
    minZ: float | None = None

    # Holds our current layer number
    currentLayer = -1

    # Indicates if we're only supposed to apply our settings to a single layer or multiple layers
    applyToSingleLayer = False

    # Indicates if this should emit the changes as they happen to the LCD
    displayChangesToLcd = False

    # Indicates that this mod is still enabled (or not)
    enabled = True

    # Indicates if we're processing inside the target layer or not
    insideTargetArea = False

    # Indicates if we have restored the previous values from before we started our pass
    originalValuesRestored = False

    # Indicates if the user has opted for linear move retractions or firmware retractions
    linearRetraction = True

    # Indicates if we're targeting by layer or height value
    targetByLayer = True

    # Indicates if we have injected our changed values for the given layer yet
    targetValuesInjected = False

    # Holds the last extrusion value, used with detecting when a retraction is made
    lastE: float | None = None

    # An index of our gcodes which we're monitoring
    lastValues = {}

    # The detected layer height from the gcode
    layerHeight: float | None = None

    # What later to start at
    targetLayerStart: int | None = None

    # What later to end at
    targetLayerEnd: int | None = None

    # Holds the values the user has requested to change
    targetValues = {}

    # The minimum cumulative layer height at which to start modifications
    targetZStart: float | None = None
    
    # The minimum cumulative layer height at which to stop modifications
    targetZEnd: float | None = None    

    # Used to track if we've been inside our target layer yet
    leftTargetArea = False

    # Used to help detect early if we should process a line or not
    __supportedCodes = {"G0", "G1", "M104", "M106", "M140", "M141", "M207", "M220", "M221"}

    # boots up the class with defaults
    def __init__(self):
        self.reset()

    # Sets the flags if we're at the target layer or not
    def detectTargetArea(self):

        inside_target_area = self.isInsideTargetArea()

        if inside_target_area == self.insideTargetArea:
            return

        self.leftTargetArea |= self.insideTargetArea and not inside_target_area

        self.insideTargetArea = inside_target_area

        if self.insideTargetArea:
            Logger.info("Inside target area on layer: %s", self.currentLayer)
        elif self.leftTargetArea:
            Logger.info("Left target area on layer: %s", self.currentLayer)

    # Modifies the given GCODE and injects the commands at the various targets
    def execute(self, sections: list[str]):
        global executions

        # shortcut the whole thing if we're not enabled
        if not self.enabled:
            Logger.info("ChangeAtZ with settings is not enabled: %s", self)
            return sections

        Logger.info("Running ChangeAtZ with settings: %s", self)

        # our layer cursor
        index = 0

        # the first "layer" is actually the header of the gcode and not a layer by definition
        # so we'll start at -1
        layer_number = -1

        for current_section in sections:
            Logger.info("---------------------------------------")

            # break apart the section into commands
            lines = current_section.strip().split("\n")

            self.readLayerSettings(lines)

            modified_lines = []

            modified_lines.extend(self.getTargetGCode())
            modified_lines.extend(self.getLineChanges(lines))
            modified_lines.extend(self.getOriginalGCode())

            sections[index] = "\n".join(modified_lines).strip() + "\n"

            layer_number += 1
            index += 1

        # return our modified gcode
        return sections

    def firstNotNone(self, *args):
        for x in args:
            if x is not None:
                return x

    # Builds the restored layer settings based on the previous settings and returns the relevant GCODE lines
    def getChangedLastValues(self) -> dict[str, any]:

        # capture the values that we've changed
        changed = {}

        # for each of our target values, get the value to restore
        # no point in restoring values we haven't changed
        for key in self.targetValues:

            # skip target values we can't restore
            if key not in self.lastValues:
                continue

            # save into our changed
            changed[key] = self.lastValues[key]

        # return our collection of changed values
        return changed

    # Builds the relevant display feedback for each of the values
    def getDisplayGCodeFromValues(self, values: dict[str, any]) -> list[str]:

        # stop here if we're not outputting data
        if not self.displayChangesToLcd:
            return []

        display_text = []

        # looking for wait for bed temp
        if "bedTemp" in values:
            display_text.append("Bed Temp: " + str(round(values["bedTemp"])))

        # looking for wait for Build Volume Temperature
        if "buildVolumeTemperature" in values:
            display_text.append("Build Volume Temperature: " + str(round(values["buildVolumeTemperature"])))

        # set our extruder one temp (if specified)
        if "extruderOne" in values:
            display_text.append("Extruder 1 Temp: " + str(round(values["extruderOne"])))

        # set our extruder two temp (if specified)
        if "extruderTwo" in values:
            display_text.append("Extruder 2 Temp: " + str(round(values["extruderTwo"])))

        # set global flow rate
        if "flowrate" in values:
            display_text.append("Extruder A Flow Rate: " + str(values["flowrate"]))

        # set extruder 0 flow rate
        if "flowrateOne" in values:
            display_text.append("Extruder 1 Flow Rate: " + str(values["flowrateOne"]))

        # set second extruder flow rate
        if "flowrateTwo" in values:
            display_text.append("Extruder 2 Flow Rate: " + str(values["flowrateTwo"]))

        # set our fan speed
        if "fanSpeed" in values:
            display_text.append("Fan Speed: " + str(values["fanSpeed"]))

        # set feedrate percentage
        if "speed" in values:
            display_text.append("Print Speed: " + str(values["speed"]))

        # set print rate percentage
        if "printspeed" in values:
            display_text.append("Linear Print Speed: " + str(values["printspeed"]))

        # set retract rate
        if "retractfeedrate" in values:
            display_text.append("Retract Feed Rate: " + str(values["retractfeedrate"]))

        # set retract length
        if "retractlength" in values:
            display_text.append("Retract Length: " + str(values["retractlength"]))

        # stop here if there's nothing to output
        if len(display_text) == 0:
            return []

        # output our command to display the data
        return ["M117 " + ", ".join(display_text)]

    # Builds the relevant GCODE lines from the given collection of values
    def getGCodeFromValues(self, values: dict[str, any]) -> list[str]:

        # will hold all the default settings for the target layer
        codes = []

        # looking for wait for bed temp
        if "bedTemp" in values:
            codes.append("M140 S" + str(values["bedTemp"]))

        # looking for wait for Build Volume Temperature
        if "buildVolumeTemperature" in values:
            codes.append("M141 S" + str(values["buildVolumeTemperature"]))

        # set our extruder one temp (if specified)
        if "extruderOne" in values:
            codes.append("M104 S" + str(values["extruderOne"]) + " T0")

        # set our extruder two temp (if specified)
        if "extruderTwo" in values:
            codes.append("M104 S" + str(values["extruderTwo"]) + " T1")

        # set our fan speed
        if "fanSpeed" in values:
            # convert our fan speed percentage to PWM
            fan_speed = (float(values["fanSpeed"]) / 100.0) * 255.0

            # add our fan speed to the defaults
            codes.append("M106 S" + str(fan_speed))

        # set global flow rate
        if "flowrate" in values:
            codes.append("M221 S" + str(values["flowrate"]))

        # set extruder 0 flow rate
        if "flowrateOne" in values:
            codes.append("M221 S" + str(values["flowrateOne"]) + " T0")

        # set second extruder flow rate
        if "flowrateTwo" in values:
            codes.append("M221 S" + str(values["flowrateTwo"]) + " T1")

        # set feedrate percentage
        if "speed" in values:
            codes.append("M220 S" + str(values["speed"]) + "")

        # set print rate percentage
        if "printspeed" in values:
            codes.append(";PRINTSPEED " + str(values["printspeed"]) + "")

        # set retract rate
        if "retractfeedrate" in values:

            if self.linearRetraction:
                codes.append(";RETRACTFEEDRATE " + str(values["retractfeedrate"] * 60) + "")
            else:
                codes.append("M207 F" + str(values["retractfeedrate"] * 60) + "")

        # set retract length
        if "retractlength" in values:

            if self.linearRetraction:
                codes.append(";RETRACTLENGTH " + str(values["retractlength"]) + "")
            else:
                codes.append("M207 S" + str(values["retractlength"]) + "")

        return codes

    def getLastValueAsFloat(self, key: str, default: float | None = None) -> float | None:

        if not key in self.lastValues:
            return default

        return float(self.lastValues[key])

    def getLineChanges(self, lines: list[str]):

        if not self.insideTargetArea:
            return lines

        modified_lines = []

        # evaluate each command individually
        for line in lines:

            if not self.isSupportedCode(line):
                modified_lines.append(line)
                continue

            line = line.strip()

            if len(line) == 0:
                continue

            # always get our original line, otherwise the effect will be cumulative
            original_line = self.getOriginalLine(line)

            original_command = GCodeCommand.getFromLine(original_line)

            # normally special lines have comments straight from cura
            # so we'll leave those alone
            if original_command.hasComment():
                modified_lines.append(line)
                continue

            modified_command = copy.copy(original_command)

            self.processLinearMove(modified_command)
            self.processTargetValues(modified_command)

            # if no changes have been made, stop here
            if original_command == modified_command:
                modified_lines.append(line)
                continue

            # return our updated command
            modified_lines.append(self.setOriginalLine(str(modified_command), original_line))

        return modified_lines

    # generates the gcode for restoring the original values and emitting those to the printer (if desired)
    def getOriginalGCode(self) -> list[str]:

        if not self.leftTargetArea:
            return []

        if self.originalValuesRestored:
            return []

        original_values = self.getChangedLastValues()

        original_codes = self.getGCodeFromValues(original_values) + self.getDisplayGCodeFromValues(original_values)

        if len(original_codes) == 0:
            return []

        self.originalValuesRestored = True

        Logger.info("Restoring original values to layer: %s", original_values)

        # inject the defaults
        return [";[CAZD:"] + original_codes + [";:CAZD]"]

    # Returns the unmodified GCODE line from previous ChangeAtZ edits
    @staticmethod
    def getOriginalLine(line: str) -> str:

        # get the change at z original (cazo) details
        original_line = re.search(r"\[CAZO:(.*?):CAZO\]", line)

        # if we didn't get a hit, this is the original line
        if original_line is None:
            return line

        return original_line.group(1)

    # generates the gcode for overriding the existing values and emitting those to the printer (if desired)
    def getTargetGCode(self) -> list[str]:

        if not self.insideTargetArea:
            return []

        if self.targetValuesInjected:
            return []

        target_codes = self.getGCodeFromValues(self.targetValues) + self.getDisplayGCodeFromValues(self.targetValues)

        if len(target_codes) == 0:
            return []

        self.targetValuesInjected = True

        Logger.info("Applying target values to layer: %s", self.targetValues)

        # inject the defaults
        return [";[CAZD:"] + target_codes + [";:CAZD]"]

    def getTargetValueAsInt(self, key: str, default: int | None = None) -> int | None:

        if not key in self.targetValues:
            return default

        return int(self.targetValues[key])

    def getTargetValueAsFloat(self, key: str, default: float | None = None) -> float | None:

        if not key in self.targetValues:
            return default

        return float(self.targetValues[key])

    # Determines if the current line is at or below the target required to start modifying
    def isInsideTargetArea(self) -> bool:

        if not self.targetByLayer:
        
            if self.minZ is None:
                return False
        
            if self.applyToSingleLayer:
                return self.minZ == self.targetZStart
            else:
                return self.minZ >= self.targetZStart and (self.targetZEnd == -1 or self.minZ < self.targetZEnd)

        if self.currentLayer is None:
            return False

        # if we're applying to a single layer, stop if our layer is not identical
        if self.applyToSingleLayer:
            return self.currentLayer == self.targetLayerStart
        else:
            return self.currentLayer >= self.targetLayerStart and (self.targetLayerEnd == -1 or self.currentLayer < self.targetLayerEnd)

    def isSupportedCode(self, line: str) -> bool:
        """
        Allows the plugin to skip lines that it doesn't care about
        """
        for supportedCode in self.__supportedCodes:
            if line.startswith(supportedCode + " "):
                return True

        return False

    def maxNotNone(self, *args) -> float:
        return max(x for x in args if x is not None)

    def minNotNone(self, *args) -> float:
        return min(x for x in args if x is not None)

    # Handles any linear moves in the current line
    def processLinearMove(self, modified_command: GCodeCommand):

        if not modified_command.isLinearMove():
            return

        # handle retract length
        self.processRetractLength(modified_command)

        # handle retract feed rate
        self.processRetractFeedRate(modified_command)

        # handle print speed adjustments
        self.processPrintSpeed(modified_command)

        # set our current extrude position
        self.lastE = self.firstNotNone(modified_command.getArgumentAsFloat("E"), self.lastE)

    def processTargetValues(self, modified_command: GCodeCommand):

        if modified_command.isLinearMove():
            return

        if modified_command.command == "M104":
            extruder = modified_command.getArgumentAsInt("T")

            if extruder is None:
                return

            feed_rate = None

            if extruder == 0:
                feed_rate = self.getTargetValueAsFloat("extruderOne")
            elif extruder == 1:
                feed_rate = self.getTargetValueAsFloat("extruderTwo")

            if feed_rate is None:
                return

            modified_command.setArgument("S", feed_rate)
            return

        if modified_command.command == "M106":
            fan_speed = self.getTargetValueAsFloat("fanSpeed")

            if fan_speed is None:
                return

            modified_command.setArgument("S", (fan_speed / 100.0) * 255.0)
            return

        if modified_command.command == "M140":
            bed_temp = self.getTargetValueAsFloat("bedTemp")

            if bed_temp is None:
                return

            modified_command.setArgument("S", bed_temp)
            return

        if modified_command.command == "M141":
            build_volume_temp = self.getTargetValueAsFloat("buildVolumeTemperature")

            if build_volume_temp is None:
                return

            modified_command.setArgument("S", build_volume_temp)
            return

        if modified_command.command == "M207":
            retract_feed_rate = self.getTargetValueAsFloat("retractfeedrate")

            if not retract_feed_rate is None:
                modified_command.setArgument("F", retract_feed_rate)

            retract_length = self.getTargetValueAsFloat("retractlength")

            if not retract_length is None:
                modified_command.setArgument("S", retract_length)

            return

        if modified_command.command == "M220":
            feed_rate = self.getTargetValueAsFloat("speed")

            if feed_rate is None:
                return

            modified_command.setArgument("S", feed_rate)
            return

        if modified_command.command == "M221":
            extruder = modified_command.getArgumentAsInt("T")

            if extruder is None:
                return

            flow_rate = None

            if extruder == 0:
                flow_rate = self.getTargetValueAsFloat("flowrateOne")
            elif extruder == 1:
                flow_rate = self.getTargetValueAsFloat("flowrateTwo")

            if flow_rate is None:
                return

            modified_command.setArgument("S", flow_rate)
            return

    # Handles any changes to print speed for the given linear motion command
    def processPrintSpeed(self, modified_command: GCodeCommand):

        print_speed = self.getTargetValueAsInt("printspeed")

        # if we're not setting print speed or we don't have a feed rate, stop here
        if print_speed is None:
            return

        feed_rate = modified_command.getArgumentAsFloat("F")

        if feed_rate is None:
            return

        # if they requested no change to print speed (ie: 100%), stop here
        if print_speed == 100:
            return

        # get our feed rate from the command
        feed_rate *= (float(print_speed) / float(100.0))

        modified_command.setArgument("F", int(feed_rate))

    # Handles any changes to retraction length for the given linear motion command
    def processRetractLength(self, modified_command: GCodeCommand):

        # if we don't have a retract length in the file we can't add one
        if "retractlength" not in self.lastValues or self.lastValues["retractlength"] == 0:
            return

        # if we're not changing retraction length, stop here
        if "retractlength" not in self.targetValues:
            return

        if not modified_command.isRetraction():
            return

        # stop here if we don't know our last extrude value
        if self.lastE is None:
            return

        extrude_length = modified_command.getArgumentAsFloat("E")

        # if there's no change in extrude we have nothing to change
        if self.lastE == extrude_length:
            return

        # if our last extrude was lower than our current, we're restoring, so skip
        if self.lastE < extrude_length:
            return

        # get our desired retract length
        retract_length = self.getTargetValueAsFloat("retractlength")

        # subtract the difference between the default and the desired
        extrude_length -= (retract_length - self.getLastValueAsFloat("retractlength"))

        # replace our extrude amount
        modified_command.setArgument("E", extrude_length)

    # Handles any changes to retraction feed rate for the given linear motion command
    def processRetractFeedRate(self, modified_command: GCodeCommand):

        # skip if we're not doing linear retractions
        if not self.linearRetraction:
            return

        # get our desired retract feed rate
        retract_feed_rate = self.getTargetValueAsFloat("retractfeedrate")

        # if we're not changing retraction length, stop here
        if retract_feed_rate is None:
            return

        if not modified_command.isRetraction():
            return

        # convert to units/min
        retract_feed_rate *= 60

        modified_command.setArgument("F", retract_feed_rate)

    # Tracks the change in gcode values we're interested in
    def readChangeableSettings(self, line: str):

        # simulate a print speed command
        if ";PRINTSPEED" in line:
            line = line.replace(";PRINTSPEED ", "M220 S")

        # simulate a retract feedrate command
        if ";RETRACTFEEDRATE" in line:
            line = line.replace(";RETRACTFEEDRATE ", "M207 F")

        # simulate a retract length command
        if ";RETRACTLENGTH" in line:
            line = line.replace(";RETRACTLENGTH ", "M207 S")

        # get our gcode command
        command = GCodeCommand.getFromLine(line)

        # stop here if it isn't a G or M command
        if command is None:
            return

        # handle bed temp changes
        if command.command == "M140" or command.command == "M190":

            # get our bed temp if provided
            if command.hasArgument("S"):
                self.setLastValue("bedTemp", command.getArgumentAsFloat("S"))

            # move to the next command
            return

        # handle Build Volume Temperature changes, really shouldn't want to wait for enclosure temp mid print though.
        if command.command == "M141" or command.command == "M191":

            # get our bed temp if provided
            if command.hasArgument("S"):
                self.setLastValue("buildVolumeTemperature", command.getArgumentAsFloat("S"))

            # move to the next command
            return

        # handle extruder temp changes
        if command.command == "M104" or command.command == "M109":

            # get our temperature
            temperature = command.getArgumentAsFloat("S")

            # don't bother if we don't have a temperature
            if temperature is None:
                return

            # get our extruder, default to extruder one
            extruder = command.getArgumentAsInt("T", None)

            # set our extruder temp based on the extruder
            if extruder is None or extruder == 0:
                self.setLastValue("extruderOne", temperature)

            if extruder is None or extruder == 1:
                self.setLastValue("extruderTwo", temperature)

            # move to the next command
            return

        # handle fan speed changes
        if command.command == "M106":

            if command.hasArgument("S"):
                # allow up to 2 decimals of precision by multiplying by 10,000 and cropping off the rest
                self.setLastValue("fanSpeed", floor((command.getArgumentAsFloat("S") / float(255.0)) * 10000) / 100)

            # move to the next command
            return

        # handle flow rate changes
        if command.command == "M221":

            # get our flow rate
            temperature = command.getArgumentAsFloat("S")

            # don't bother if we don't have a flow rate (for some reason)
            if temperature is None:
                return

            # get our extruder, default to global
            extruder = command.getArgumentAsInt("T", None)

            # set our extruder temp based on the extruder
            if extruder is None:
                self.setLastValue("flowrate", temperature)
            elif extruder == 1:
                self.setLastValue("flowrateOne", temperature)
            elif extruder == 1:
                self.setLastValue("flowrateTwo", temperature)

            # move to the next command
            return

        # handle print speed changes
        if command.command == "M220":

            # get our speed if provided
            if command.hasArgument("S"):
                self.setLastValue("speed", command.getArgumentAsFloat("S"))

            # move to the next command
            return

        # check our retract length
        self.readRetractLengthSetting(command)

    # Used for finding settings in the print file before we process anything else
    def readCuraSettings(self, line: str):

        current_layer = GCodeCommand.getCommentArgumentAsInt(line, ";LAYER:", self.currentLayer)

        if current_layer != self.currentLayer:
            # resetting min Z so we get the new floor for the layer
            self.minZ = self.currentZ

            self.currentLayer = current_layer

        # if we're in layers already we're out of settings
        if self.currentLayer >= 0:
            return

        self.layerHeight = GCodeCommand.getCommentArgumentAsFloat(line, ";Layer height:", self.layerHeight)

    # Grabs the current height
    def readCurrentZ(self, line: str):

        # stop here if we haven't left the header yet
        if self.currentLayer < 0:
            return

        command = GCodeCommand.getLinearMoveCommand(line)

        # stop here if this isn't a linear move command
        if command is None:
            return

        command_z = command.getArgumentAsFloat("Z")

        self.currentZ = self.firstNotNone(command_z, self.currentZ)

        self.minZ = self.minNotNone(self.currentZ, self.minZ)

    def readLayerSettings(self, lines: list[str]):
        """
        This is used for detecting things like the current layer Z min and the layer height
        but also determining if we should target this layer or not
        """

        for line in lines:

            line = line.strip()

            if len(line) == 0:
                continue

            self.readCuraSettings(line)

            self.readCurrentZ(line)

            self.readChangeableSettings(line)

        Logger.info("Layer: %s", self.currentLayer)
        Logger.info("Layer Height: %s", self.layerHeight)
        Logger.info("Min Z: %s", self.minZ)

        self.detectTargetArea()

    # Used for picking out the retract length set by Cura
    def readRetractLengthSetting(self, command: GCodeCommand):

        # handle retract length changes
        if command.command == "M207":

            # get our retract length if provided
            if command.hasArgument("S"):
                self.setLastValue("retractlength", command.getArgumentAsFloat("S"))

            # get our retract feedrate if provided, convert from mm/m to mm/s
            if command.hasArgument("F"):
                self.setLastValue("retractfeedrate", command.getArgumentAsFloat("F") / 60.0)

            # move to the next command
            return

        # skip if we're not doing linear retractions
        if not self.linearRetraction:
            return

        # get our command from the line
        command = command.asLinearMove()

        # if it's not a linear move, we don't care
        if command is None:
            return

        # get our linear move parameters
        feed_rate = command.getArgumentAsFloat("F")
        x_coord = command.getArgumentAsFloat("X")
        y_coord = command.getArgumentAsFloat("Y")
        z_coord = command.getArgumentAsFloat("Z")
        extrude_length = command.getArgumentAsFloat("E")

        # the command we're looking for only has extrude and feed rate
        if x_coord is not None or y_coord is not None or z_coord is not None:
            return

        # if either extrude or feed is missing we're likely looking at the wrong command
        if extrude_length is None or feed_rate is None:
            return

        # cura stores the retract length as a negative E just before it starts printing
        extrude_length = extrude_length * -1

        # if it's a negative extrude after being inverted, it's not our retract length
        if extrude_length < 0:
            return

        extrude_length = self.maxNotNone(self.getLastValueAsFloat("retractlength"), abs(extrude_length))
        self.setLastValue("retractlength", extrude_length)

    # Resets the class contents to defaults
    def reset(self):

        self.targetValues = {}
        self.applyToSingleLayer = False
        self.lastE = None
        self.currentZ = 0
        self.minZ = None
        self.currentLayer = -1
        self.targetByLayer = True
        self.targetLayerStart = None
        self.targetLayerEnd = None
        self.targetZStart = None
        self.targetZEnd = None
        self.lastValues = {"speed": 100}
        self.linearRetraction = True
        self.insideTargetArea = False
        self.targetValuesInjected = False
        self.originalValuesRestored = False
        self.leftTargetArea = False
        self.enabled = True

    def setLastValue(self, key: str, new_value: any) -> any:
        """
        Used to keep track of and log value changes for sanity
        """
        current_value = self.lastValues.get(key, None)

        if current_value == new_value:
            return current_value

        self.lastValues[key] = new_value

        Logger.info("Got new value for %s: %s", key, new_value)

    # Sets the original GCODE line in a given GCODE command
    @staticmethod
    def setOriginalLine(line, original) -> str:
        return line + ";[CAZO:" + original + ":CAZO]"


    def __str__(self):
        return json.dumps({"targetValues": self.targetValues, "applyToSingleLayer": self.applyToSingleLayer,
                           "targetByLayer": self.targetByLayer, "targetLayerStart": self.targetLayerStart,
                           "targetLayerEnd": self.targetLayerEnd, "targetZStart": self.targetZStart,
                           "targetZEnd": self.targetZEnd,
                           "linearRetraction": self.linearRetraction, "enabled": self.enabled})
