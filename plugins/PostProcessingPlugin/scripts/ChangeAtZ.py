# ChangeAtZ script - Change printing parameters at a given height
# This script is the successor of the TweakAtZ plugin for legacy Cura.
# It contains code from the TweakAtZ plugin V1.0-V4.x and from the ExampleScript by Jaime van Kessel, Ultimaker B.V.
# It runs with the PostProcessingPlugin which is released under the terms of the AGPLv3 or higher.
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

# Authors of the ChangeAtZ plugin / script:
# Written by Steven Morlock, smorloc@gmail.com
# Modified by Ricardo Gomez, ricardoga@otulook.com, to add Bed Temperature and make it work with Cura_13.06.04+
# Modified by Stefan Heule, Dim3nsioneer@gmx.ch since V3.0 (see changelog below)
# Modified by Jaime van Kessel (Ultimaker), j.vankessel@ultimaker.com to make it work for 15.10 / 2.x
# Modified by Ruben Dulek (Ultimaker), r.dulek@ultimaker.com, to debug.
# Modified by Wes Hanney, https://github.com/novamxd, Retract Length + Speed, Clean up

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
# V5.0.1:	Bugfix for calling unknown property 'bedTemp' of previous settings storage and unkown variable 'speed'
# V5.1:		API Changes included for use with Cura 2.2
# V5.2.0:	Wes Hanney. Added support for changing Retract Length and Speed. Removed layer spread option. Fixed issue of cumulative ChangeZ
# mods so they can now properly be stacked on top of each other. Applied code refactoring to clean up various coding styles. Added comments.
# Broke up functions for clarity. Split up class so it can be debugged outside of Cura.
# V5.2.1:	Wes Hanney. Added support for firmware based retractions. Fixed issue of properly restoring previous values in single layer option.
# Added support for outputting changes to LCD (untested). Added type hints to most functions and variables. Added more comments. Created GCodeCommand
# class for better detection of G1 vs G10 or G11 commands, and accessing arguments. Moved most GCode methods to GCodeCommand class. Improved wording
# of Single Layer vs Keep Layer to better reflect what was happening.

# Uses -
# M220 S<factor in percent> - set speed factor override percentage
# M221 S<factor in percent> - set flow factor override percentage
# M221 S<factor in percent> T<0-#toolheads> - set flow factor override percentage for single extruder
# M104 S<temp> T<0-#toolheads> - set extruder <T> to target temperature <S>
# M140 S<temp> - set bed target temperature
# M106 S<PWM> - set fan speed to target speed <S>
# M207 S<mm> F<mm/m> - set the retract length <S> or feed rate <F>
# M117 - output the current changes

from typing import List, Dict
from ..Script import Script
import re


# this was broken up into a separate class so the main ChangeZ script could be debugged outside of Cura
class ChangeAtZ(Script):
    version = "5.2.1"

    def getSettingDataString(self):
        return """{
            "name": "ChangeAtZ """ + self.version + """(Experimental)",
            "key": "ChangeAtZ",
            "metadata": {},
            "version": 2,
            "settings": {
                "caz_enabled": {
                    "label": "Enabled",
                    "description": "Allows adding multiple ChangeZ mods and disabling them as needed.",
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
                    "label": "Change Height",
                    "description": "Z height to change at",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": "0",
                    "minimum_value_warning": "0.1",
                    "maximum_value_warning": "230",
                    "enabled": "a_trigger == 'height'"
                },
                "b_targetL": {
                    "label": "Change Layer",
                    "description": "Layer no. to change at",
                    "unit": "",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": "-100",
                    "minimum_value_warning": "-1",
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
                    "label": "Change Speed",
                    "description": "Select if total speed (print and travel) has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "e2_speed": {
                    "label": "Speed",
                    "description": "New total speed (print and travel)",
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
                    "description": "Select if print speed has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "f2_printspeed": {
                    "label": "Print Speed",
                    "description": "New print speed",
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
                    "description": "Select if flow rate has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "g2_flowrate": {
                    "label": "Flow Rate",
                    "description": "New Flow rate",
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
                    "description": "Select if first extruder flow rate has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "g4_flowrateOne": {
                    "label": "Flow Rate One",
                    "description": "New Flow rate Extruder 1",
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
                    "description": "Select if second extruder flow rate has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "g6_flowrateTwo": {
                    "label": "Flow Rate two",
                    "description": "New Flow rate Extruder 2",
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
                    "description": "Select if Bed Temperature has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "h2_bedTemp": {
                    "label": "Bed Temp",
                    "description": "New Bed Temperature",
                    "unit": "C",
                    "type": "float",
                    "default_value": 60,
                    "minimum_value": "0",
                    "minimum_value_warning": "30",
                    "maximum_value_warning": "120",
                    "enabled": "h1_Change_bedTemp"
                },
                "i1_Change_extruderOne": {
                    "label": "Change Extruder 1 Temp",
                    "description": "Select if First Extruder Temperature has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "i2_extruderOne": {
                    "label": "Extruder 1 Temp",
                    "description": "New First Extruder Temperature",
                    "unit": "C",
                    "type": "float",
                    "default_value": 190,
                    "minimum_value": "0",
                    "minimum_value_warning": "160",
                    "maximum_value_warning": "250",
                    "enabled": "i1_Change_extruderOne"
                },
                "i3_Change_extruderTwo": {
                    "label": "Change Extruder 2 Temp",
                    "description": "Select if Second Extruder Temperature has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "i4_extruderTwo": {
                    "label": "Extruder 2 Temp",
                    "description": "New Second Extruder Temperature",
                    "unit": "C",
                    "type": "float",
                    "default_value": 190,
                    "minimum_value": "0",
                    "minimum_value_warning": "160",
                    "maximum_value_warning": "250",
                    "enabled": "i3_Change_extruderTwo"
                },
                "j1_Change_fanSpeed": {
                    "label": "Change Fan Speed",
                    "description": "Select if Fan Speed has to be changed",
                    "type": "bool",
                    "default_value": false
                },
                "j2_fanSpeed": {
                    "label": "Fan Speed",
                    "description": "New Fan Speed (0-100)",
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
                    "description": "Indicates you would like to modify retraction properties.",
                    "type": "bool",
                    "default_value": false
                },                  
                "caz_retractstyle": {
                    "label": "Retract Style",
                    "description": "Specify if you're using firmware retraction or linear move based retractions. Check your printer settings to see which you're using.",
                    "type": "enum",
                    "options": {
                        "linear": "Linear Move",                       
                        "firmware": "Firmware"
                    },
                    "default_value": "linear",
                    "enabled": "caz_change_retract"
                },                  
                "caz_change_retractfeedrate": {
                    "label": "Change Retract Feed Rate",
                    "description": "Changes the retraction feed rate during print",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "caz_change_retract"
                },                
                "caz_retractfeedrate": {
                    "label": "Retract Feed Rate",
                    "description": "New Retract Feed Rate (mm/s)",
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
                    "description": "Changes the retraction length during print",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "caz_change_retract"
                },
                "caz_retractlength": {
                    "label": "Retract Length",
                    "description": "New Retract Length (mm)",
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

    def execute(self, data):

        caz_instance = ChangeAtZProcessor()

        caz_instance.TargetValues = {}

        # copy over our settings to our change z class
        self.setIntSettingIfEnabled(caz_instance, "e1_Change_speed", "speed", "e2_speed")
        self.setIntSettingIfEnabled(caz_instance, "f1_Change_printspeed", "printspeed", "f2_printspeed")
        self.setIntSettingIfEnabled(caz_instance, "g1_Change_flowrate", "flowrate", "g2_flowrate")
        self.setIntSettingIfEnabled(caz_instance, "g3_Change_flowrateOne", "flowrateOne", "g4_flowrateOne")
        self.setIntSettingIfEnabled(caz_instance, "g5_Change_flowrateTwo", "flowrateTwo", "g6_flowrateTwo")
        self.setFloatSettingIfEnabled(caz_instance, "h1_Change_bedTemp", "bedTemp", "h2_bedTemp")
        self.setFloatSettingIfEnabled(caz_instance, "i1_Change_extruderOne", "extruderOne", "i2_extruderOne")
        self.setFloatSettingIfEnabled(caz_instance, "i3_Change_extruderTwo", "extruderTwo", "i4_extruderTwo")
        self.setIntSettingIfEnabled(caz_instance, "j1_Change_fanSpeed", "fanSpeed", "j2_fanSpeed")
        self.setFloatSettingIfEnabled(caz_instance, "caz_change_retractfeedrate", "retractfeedrate", "caz_retractfeedrate")
        self.setFloatSettingIfEnabled(caz_instance, "caz_change_retractlength", "retractlength", "caz_retractlength")

        # is this mod enabled?
        caz_instance.IsEnabled = self.getSettingValueByKey("caz_enabled")

        # are we emitting data to the LCD?
        caz_instance.IsDisplayingChangesToLcd = self.getSettingValueByKey("caz_output_to_display")

        # are we doing linear move retractions?
        caz_instance.IsLinearRetraction = self.getSettingValueByKey("caz_retractstyle") == "linear"

        # see if we're applying to a single layer or to all layers hence forth
        caz_instance.IsApplyToSingleLayer = self.getSettingValueByKey("c_behavior") == "single_layer"

        # used for easy reference of layer or height targeting
        caz_instance.IsTargetByLayer = self.getSettingValueByKey("a_trigger") == "layer_no"

        # change our target based on what we're targeting
        caz_instance.TargetLayer = self.getIntSettingByKey("b_targetL", None)
        caz_instance.TargetZ = self.getFloatSettingByKey("b_targetZ", None)

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
        caz_instance.TargetValues[target] = value

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
        caz_instance.TargetValues[target] = value

    # Returns the given settings value as an integer or the default if it cannot parse it
    def getIntSettingByKey(self, key, default):

        # change our target based on what we're targeting
        try:
            return int(self.getSettingValueByKey(key))
        except:
            return default

    # Returns the given settings value as an integer or the default if it cannot parse it
    def getFloatSettingByKey(self, key, default):

        # change our target based on what we're targeting
        try:
            return float(self.getSettingValueByKey(key))
        except:
            return default


# This is a utility class for getting details of gcodes from a given line
class GCodeCommand:

    # The GCode command itself (ex: G10)
    Command = None,

    # Contains any arguments passed to the command. The key is the argument name, the value is the value of the argument.
    Arguments = {}

    # Contains the components of the command broken into pieces
    Components = []

    # Constructor. Sets up defaults
    def __init__(self):
        self.reset()

    # Gets a GCode Command from the given single line of GCode
    @staticmethod
    def getFromLine(line: str):

        # obviously if we don't have a command, we can't return anything
        if line is None or len(line) == 0:
            return None

        # we only support G or M commands
        if line[0] != "G" and line[0] != "M":
            return None

        # remove any comments
        line = re.sub(r";.*$", "", line)

        # break into the individual components
        command_pieces = line.strip().split(" ")

        # our return command details
        command = GCodeCommand()

        # stop here if we don't even have something to interpret
        if len(command_pieces) == 0:
            return None

        # stores all the components of the command within the class for later
        command.Components = command_pieces

        # set the actual command
        command.Command = command_pieces[0]

        # stop here if we don't have any parameters
        if len(command_pieces) == 1:
            return None

        # return our indexed command
        return command

    # Handy function for reading a linear move command
    @staticmethod
    def getLinearMoveCommand(line: str):

        # get our command from the line
        linear_command = GCodeCommand.getFromLine(line)

        # if it's not a linear move, we don't care
        if linear_command is None or (linear_command.Command != "G0" and linear_command.Command != "G1"):
            return None

        # convert our values to floats (or defaults)
        linear_command.Arguments["F"] = linear_command.getArgumentAsFloat("F", None)
        linear_command.Arguments["X"] = linear_command.getArgumentAsFloat("X", None)
        linear_command.Arguments["Y"] = linear_command.getArgumentAsFloat("Y", None)
        linear_command.Arguments["Z"] = linear_command.getArgumentAsFloat("Z", None)
        linear_command.Arguments["E"] = linear_command.getArgumentAsFloat("E", None)

        # return our new command
        return linear_command

    # Gets the value of a parameter or returns the default if there is none
    def getArgument(self, name: str, default: str = None) -> str:

        # parse our arguments (only happens once)
        self.parseArguments()

        # if we don't have the parameter, return the default
        if name not in self.Arguments:
            return default

        # otherwise return the value
        return self.Arguments[name]

    # Gets the value of a parameter as a float or returns the default
    def getArgumentAsFloat(self, name: str, default: float = None) -> float:

        # try to parse as a float, otherwise return the default
        try:
            return float(self.getArgument(name, default))
        except:
            return default

    # Gets the value of a parameter as an integer or returns the default
    def getArgumentAsInt(self, name: str, default: int = None) -> int:

        # try to parse as a integer, otherwise return the default
        try:
            return int(self.getArgument(name, default))
        except:
            return default

    # Allows retrieving values from the given GCODE line
    @staticmethod
    def getDirectArgument(line: str, key: str, default: str = None) -> str:

        if key not in line or (";" in line and line.find(key) > line.find(";") and ";ChangeAtZ" not in key and ";LAYER:" not in key):
            return default

        # allows for string lengths larger than 1
        sub_part = line[line.find(key) + len(key):]

        if ";ChangeAtZ" in key:
            m = re.search("^[0-4]", sub_part)
        elif ";LAYER:" in key:
            m = re.search("^[+-]?[0-9]*", sub_part)
        else:
            # the minus at the beginning allows for negative values, e.g. for delta printers
            m = re.search(r"^[-]?[0-9]*\.?[0-9]*", sub_part)
        if m is None:
            return default

        try:
            return m.group(0)
        except:
            return default

    # Converts the command parameter to a int or returns the default
    @staticmethod
    def getDirectArgumentAsFloat(line: str, key: str, default: float = None) -> float:

        # get the value from the command
        value = GCodeCommand.getDirectArgument(line, key, default)

        # stop here if it's the default
        if value == default:
            return value

        try:
            return float(value)
        except:
            return default

    # Converts the command parameter to a int or returns the default
    @staticmethod
    def getDirectArgumentAsInt(line: str, key: str, default: int = None) -> int:

        # get the value from the command
        value = GCodeCommand.getDirectArgument(line, key, default)

        # stop here if it's the default
        if value == default:
            return value

        try:
            return int(value)
        except:
            return default

    # Parses the arguments of the command on demand, only once
    def parseArguments(self):

        # stop here if we don't have any remaining components
        if len(self.Components) <= 1:
            return None

        # iterate and index all of our parameters, skip the first component as it's the command
        for i in range(1, len(self.Components)):

            # get our component
            component = self.Components[i]

            # get the first character of the parameter, which is the name
            component_name = component[0]

            # get the value of the parameter (the rest of the string
            component_value = None

            # get our value if we have one
            if len(component) > 1:
                component_value = component[1:]

            # index the argument
            self.Arguments[component_name] = component_value

        # clear the components to we don't process again
        self.Components = []

    # Easy function for replacing any GCODE parameter variable in a given GCODE command
    @staticmethod
    def replaceDirectArgument(line: str, key: str, value: str) -> str:
        return re.sub(r"(^|\s)" + key + r"[\d\.]+(\s|$)", r"\1" + key + str(value) + r"\2", line)

    # Resets the model back to defaults
    def reset(self):
        self.Command = None
        self.Arguments = {}


# The primary ChangeAtZ class that does all the gcode editing. This was broken out into an
# independent class so it could be debugged using a standard IDE
class ChangeAtZProcessor:

    # Holds our current height
    CurrentZ = None

    # Holds our current layer number
    CurrentLayer = None

    # Indicates if we're only supposed to apply our settings to a single layer or multiple layers
    IsApplyToSingleLayer = False

    # Indicates if this should emit the changes as they happen to the LCD
    IsDisplayingChangesToLcd = False

    # Indicates that this mod is still enabled (or not)
    IsEnabled = True

    # Indicates if we're processing inside the target layer or not
    IsInsideTargetLayer = False

    # Indicates if we have restored the previous values from before we started our pass
    IsLastValuesRestored = False

    # Indicates if the user has opted for linear move retractions or firmware retractions
    IsLinearRetraction = True

    # Indicates if we're targetting by layer or height value
    IsTargetByLayer = True

    # Indicates if we have injected our changed values for the given layer yet
    IsTargetValuesInjected = False

    # Holds the last extrusion value, used with detecting when a retraction is made
    LastE = None

    # An index of our gcodes which we're monitoring
    LastValues = {}

    # The detected layer height from the gcode
    LayerHeight = None

    # The target layer
    TargetLayer = None

    # Holds the values the user has requested to change
    TargetValues = {}

    # The target height in mm
    TargetZ = None

    # Used to track if we've been inside our target layer yet
    WasInsideTargetLayer = False

    # boots up the class with defaults
    def __init__(self):
        self.reset()

    # Modifies the given GCODE and injects the commands at the various targets
    def execute(self, data):

        # short cut the whole thing if we're not enabled
        if not self.IsEnabled:
            return data

        # our layer cursor
        index = 0

        for active_layer in data:

            # will hold our updated gcode
            modified_gcode = ""

            # mark all the defaults for deletion
            active_layer = self.markChangesForDeletion(active_layer)

            # break apart the layer into commands
            lines = active_layer.split("\n")

            # evaluate each command individually
            for line in lines:

                # trim or command
                line = line.strip()

                # skip empty lines
                if len(line) == 0:
                    continue

                # update our layer number if applicable
                self.processLayerNumber(line)

                # update our layer height if applicable
                self.processLayerHeight(line)

                # check if we're at the target layer or not
                self.processTargetLayer()

                # process any changes to the gcode
                modified_gcode += self.processLine(line)

            # remove any marked defaults
            modified_gcode = self.removeMarkedChanges(modified_gcode)

            # append our modified line
            data[index] = modified_gcode

            index += 1

        # return our modified gcode
        return data

    # Builds the restored layer settings based on the previous settings and returns the relevant GCODE lines
    def getChangedLastValues(self) -> Dict[str, any]:

        # capture the values that we've changed
        changed = {}

        # for each of our target values, get the value to restore
        # no point in restoring values we haven't changed
        for key in self.TargetValues:

            # skip target values we can't restore
            if key not in self.LastValues:
                continue

            # save into our changed
            changed[key] = self.LastValues[key]

        # return our collection of changed values
        return changed

    # Builds the relevant display feedback for each of the values
    def getDisplayChangesFromValues(self, values: Dict[str, any]) -> str:

        # stop here if we're not outputting data
        if not self.IsDisplayingChangesToLcd:
            return ""

        # will hold all the default settings for the target layer
        codes = []

        # looking for wait for bed temp
        if "bedTemp" in values:
            codes.append("BedTemp: " + str(values["bedTemp"]))

        # set our extruder one temp (if specified)
        if "extruderOne" in values:
            codes.append("Extruder 1 Temp: " + str(values["extruderOne"]))

        # set our extruder two temp (if specified)
        if "extruderTwo" in values:
            codes.append("Extruder 2 Temp: " + str(values["extruderTwo"]))

        # set global flow rate
        if "flowrate" in values:
            codes.append("Extruder A Flow Rate: " + str(values["flowrate"]))

        # set extruder 0 flow rate
        if "flowrateOne" in values:
            codes.append("Extruder 1 Flow Rate: " + str(values["flowrateOne"]))

        # set second extruder flow rate
        if "flowrateTwo" in values:
            codes.append("Extruder 2 Flow Rate: " + str(values["flowrateTwo"]))

        # set our fan speed
        if "fanSpeed" in values:
            codes.append("Fan Speed: " + str(values["fanSpeed"]))

        # set feedrate percentage
        if "speed" in values:
            codes.append("Print Speed: " + str(values["speed"]))

        # set print rate percentage
        if "printspeed" in values:
            codes.append("Linear Print Speed: " + str(values["printspeed"]))

        # set retract rate
        if "retractfeedrate" in values:
            codes.append("Retract Feed Rate: " + str(values["retractfeedrate"]))

        # set retract length
        if "retractlength" in values:
            codes.append("Retract Length: " + str(values["retractlength"]))

        # stop here if there's nothing to output
        if len(codes) == 0:
            return ""

        # output our command to display the data
        return "M117 " + ", ".join(codes) + "\n"

    # Converts the last values to something that can be output on the LCD
    def getLastDisplayValues(self) -> str:

        # convert our last values to something we can output
        return self.getDisplayChangesFromValues(self.getChangedLastValues())

    # Converts the target values to something that can be output on the LCD
    def getTargetDisplayValues(self) -> str:

        # convert our target values to something we can output
        return self.getDisplayChangesFromValues(self.TargetValues)

    # Builds the the relevant GCODE lines from the given collection of values
    def getCodeFromValues(self, values: Dict[str, any]) -> str:

        # will hold all the desired settings for the target layer
        codes = self.getCodeLinesFromValues(values)

        # stop here if there are no values that require changing
        if len(codes) == 0:
            return ""

        # return our default block for this layer
        return ";[CAZD:\n" + "\n".join(codes) + "\n;:CAZD]"

    # Builds the relevant GCODE lines from the given collection of values
    def getCodeLinesFromValues(self, values: Dict[str, any]) -> List[str]:

        # will hold all the default settings for the target layer
        codes = []

        # looking for wait for bed temp
        if "bedTemp" in values:
            codes.append("M140 S" + str(values["bedTemp"]))

        # set our extruder one temp (if specified)
        if "extruderOne" in values:
            codes.append("M104 S" + str(values["extruderOne"]) + " T0")

        # set our extruder two temp (if specified)
        if "extruderTwo" in values:
            codes.append("M104 S" + str(values["extruderTwo"]) + " T1")

        # set our fan speed
        if "fanSpeed" in values:

            # convert our fan speed percentage to PWM
            fan_speed = int((float(values["fanSpeed"]) / 100.0) * 255)

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
            codes.append("M220 S" + str(values["speed"]) + " T1")

        # set print rate percentage
        if "printspeed" in values:
            codes.append(";PRINTSPEED " + str(values["printspeed"]) + "")

        # set retract rate
        if "retractfeedrate" in values:

            if self.IsLinearRetraction:
                codes.append(";RETRACTFEEDRATE " + str(values["retractfeedrate"] * 60) + "")
            else:
                codes.append("M207 F" + str(values["retractfeedrate"] * 60) + "")

        # set retract length
        if "retractlength" in values:

            if self.IsLinearRetraction:
                codes.append(";RETRACTLENGTH " + str(values["retractlength"]) + "")
            else:
                codes.append("M207 S" + str(values["retractlength"]) + "")

        return codes

    # Builds the restored layer settings based on the previous settings and returns the relevant GCODE lines
    def getLastValues(self) -> str:

        # build the gcode to restore our last values
        return self.getCodeFromValues(self.getChangedLastValues())

    # Builds the gcode to inject either the changed values we want or restore the previous values
    def getInjectCode(self) -> str:

        # if we're now outside of our target layer and haven't restored our last values, do so now
        if not self.IsInsideTargetLayer and self.WasInsideTargetLayer and not self.IsLastValuesRestored:

            # mark that we've injected the last values
            self.IsLastValuesRestored = True

            # inject the defaults
            return self.getLastValues() + "\n" + self.getLastDisplayValues()

        # if we're inside our target layer but haven't added our values yet, do so now
        if self.IsInsideTargetLayer and not self.IsTargetValuesInjected:

            # mark that we've injected the target values
            self.IsTargetValuesInjected = True

            # inject the defaults
            return self.getTargetValues() + "\n" + self.getTargetDisplayValues()

        # nothing to do
        return ""

    # Returns the unmodified GCODE line from previous ChangeZ edits
    @staticmethod
    def getOriginalLine(line: str) -> str:

        # get the change at z original (cazo) details
        original_line = re.search(r"\[CAZO:(.*?):CAZO\]", line)

        # if we didn't get a hit, this is the original line
        if original_line is None:
            return line

        return original_line.group(1)

    # Builds the target layer settings based on the specified values and returns the relevant GCODE lines
    def getTargetValues(self) -> str:

        # build the gcode to change our current values
        return self.getCodeFromValues(self.TargetValues)

    # Determines if the current line is at or below the target required to start modifying
    def isTargetLayerOrHeight(self) -> bool:

        # target selected by layer no.
        if self.IsTargetByLayer:

            # if we don't have a current layer, we're not there yet
            if self.CurrentLayer is None:
                return False

            # if we're applying to a single layer, stop if our layer is not identical
            if self.IsApplyToSingleLayer:
                return self.CurrentLayer == self.TargetLayer
            else:
                return self.CurrentLayer >= self.TargetLayer

        else:

            # if we don't have a current Z, we're not there yet
            if self.CurrentZ is None:
                return False

            # if we're applying to a single layer, stop if our Z is not identical
            if self.IsApplyToSingleLayer:
                return self.CurrentZ == self.TargetZ
            else:
                return self.CurrentZ >= self.TargetZ

    # Marks any current ChangeZ layer defaults in the layer for deletion
    @staticmethod
    def markChangesForDeletion(layer: str):
        return re.sub(r";\[CAZD:", ";[CAZD:DELETE:", layer)

    # Grabs the current height
    def processLayerHeight(self, line: str):

        # stop here if we haven't entered a layer yet
        if self.CurrentLayer is None:
            return

        # get our gcode command
        command = GCodeCommand.getFromLine(line)

        # skip if it's not a command we're interested in
        if command is None:
            return

        # stop here if this isn't a linear move command
        if command.Command != "G0" and command.Command != "G1":
            return

        # get our value from the command
        current_z = command.getArgumentAsFloat("Z", None)

        # stop here if we don't have a Z value defined, we can't get the height from this command
        if current_z is None:
            return

        # stop if there's no change
        if current_z == self.CurrentZ:
            return

        # set our current Z value
        self.CurrentZ = current_z

        # if we don't have a layer height yet, set it based on the current Z value
        if self.LayerHeight is None:
            self.LayerHeight = self.CurrentZ

    # Grabs the current layer number
    def processLayerNumber(self, line: str):

        # if this isn't a layer comment, stop here, nothing to update
        if ";LAYER:" not in line:
            return

        # get our current layer number
        current_layer = GCodeCommand.getDirectArgumentAsInt(line, ";LAYER:", None)

        # this should never happen, but if our layer number hasn't changed, stop here
        if current_layer == self.CurrentLayer:
            return

        # update our current layer
        self.CurrentLayer = current_layer

    # Makes any linear move changes and also injects either target or restored values depending on the plugin state
    def processLine(self, line: str) -> str:

        # used to change the given line of code
        modified_gcode = ""

        # track any values that we may be interested in
        self.trackChangeableValues(line)

        # if we're not inside the target layer, simply read the any
        # settings we can and revert any ChangeAtZ deletions
        if not self.IsInsideTargetLayer:

            # read any settings if we haven't hit our target layer yet
            if not self.WasInsideTargetLayer:
                self.processSetting(line)

            # if we haven't hit our target yet, leave the defaults as is (unmark them for deletion)
            if "[CAZD:DELETE:" in line:
                line = line.replace("[CAZD:DELETE:", "[CAZD:")

        # if we're targeting by Z, we want to add our values before the first linear move
        if "G1 " in line or "G0 " in line:
            modified_gcode += self.getInjectCode()

        # modify our command if we're still inside our target layer, otherwise pass unmodified
        if self.IsInsideTargetLayer:
            modified_gcode += self.processLinearMove(line) + "\n"
        else:
            modified_gcode += line + "\n"

        # if we're targetting by layer we want to add our values just after the layer label
        if ";LAYER:" in line:
            modified_gcode += self.getInjectCode()

        # return our changed code
        return modified_gcode

    # Handles any linear moves in the current line
    def processLinearMove(self, line: str) -> str:

        # if it's not a linear motion command we're not interested
        if not ("G1 " in line or "G0 " in line):
            return line

        # always get our original line, otherwise the effect will be cumulative
        line = self.getOriginalLine(line)

        # get our command from the line
        linear_command = GCodeCommand.getLinearMoveCommand(line)

        # if it's not a linear move, we don't care
        if linear_command is None:
            return line

        # get our linear move parameters
        feed_rate = linear_command.Arguments["F"]
        x_coord = linear_command.Arguments["X"]
        y_coord = linear_command.Arguments["Y"]
        z_coord = linear_command.Arguments["Z"]
        extrude_length = linear_command.Arguments["E"]

        # set our new line to our old line
        new_line = line

        # handle retract length
        new_line = self.processRetractLength(extrude_length, feed_rate, new_line, x_coord, y_coord, z_coord)

        # handle retract feed rate
        new_line = self.processRetractFeedRate(extrude_length, feed_rate, new_line, x_coord, y_coord, z_coord)

        # handle print speed adjustments
        if extrude_length is not None:  # Only for extrusion moves.
            new_line = self.processPrintSpeed(feed_rate, new_line)

        # set our current extrude position
        self.LastE = extrude_length if extrude_length is not None else self.LastE

        # if no changes have been made, stop here
        if new_line == line:
            return line

        # return our updated command
        return self.setOriginalLine(new_line, line)

    # Handles any changes to print speed for the given linear motion command
    def processPrintSpeed(self, feed_rate: float, new_line: str) -> str:

        # if we're not setting print speed or we don't have a feed rate, stop here
        if "printspeed" not in self.TargetValues or feed_rate is None:
            return new_line

        # get our requested print speed
        print_speed = int(self.TargetValues["printspeed"])

        # if they requested no change to print speed (ie: 100%), stop here
        if print_speed == 100:
            return new_line

        # get our feed rate from the command
        feed_rate = GCodeCommand.getDirectArgumentAsFloat(new_line, "F") * (float(print_speed) / 100.0)

        # change our feed rate
        return GCodeCommand.replaceDirectArgument(new_line, "F", feed_rate)

    # Handles any changes to retraction length for the given linear motion command
    def processRetractLength(self, extrude_length: float, feed_rate: float, new_line: str, x_coord: float, y_coord: float, z_coord: float) -> str:

        # if we don't have a retract length in the file we can't add one
        if "retractlength" not in self.LastValues or self.LastValues["retractlength"] == 0:
            return new_line

        # if we're not changing retraction length, stop here
        if "retractlength" not in self.TargetValues:
            return new_line

        # retractions are only F (feed rate) and E (extrude), at least in cura
        if x_coord is not None or y_coord is not None or z_coord is not None:
            return new_line

        # since retractions require both F and E, and we don't have either, we can't process
        if feed_rate is None or extrude_length is None:
            return new_line

        # stop here if we don't know our last extrude value
        if self.LastE is None:
            return new_line

        # if there's no change in extrude we have nothing to change
        if self.LastE == extrude_length:
            return new_line

        # if our last extrude was lower than our current, we're restoring, so skip
        if self.LastE < extrude_length:
            return new_line

        # get our desired retract length
        retract_length = float(self.TargetValues["retractlength"])

        # subtract the difference between the default and the desired
        extrude_length -= (retract_length - self.LastValues["retractlength"])

        # replace our extrude amount
        return GCodeCommand.replaceDirectArgument(new_line, "E", extrude_length)

    # Used for picking out the retract length set by Cura
    def processRetractLengthSetting(self, line: str):

        # skip if we're not doing linear retractions
        if not self.IsLinearRetraction:
            return

        # get our command from the line
        linear_command = GCodeCommand.getLinearMoveCommand(line)

        # if it's not a linear move, we don't care
        if linear_command is None:
            return

        # get our linear move parameters
        feed_rate = linear_command.Arguments["F"]
        x_coord = linear_command.Arguments["X"]
        y_coord = linear_command.Arguments["Y"]
        z_coord = linear_command.Arguments["Z"]
        extrude_length = linear_command.Arguments["E"]

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

        # what ever the last negative retract length is it wins
        self.LastValues["retractlength"] = extrude_length

    # Handles any changes to retraction feed rate for the given linear motion command
    def processRetractFeedRate(self, extrude_length: float, feed_rate: float, new_line: str, x_coord: float, y_coord: float, z_coord: float) -> str:

        # skip if we're not doing linear retractions
        if not self.IsLinearRetraction:
            return new_line

        # if we're not changing retraction length, stop here
        if "retractfeedrate" not in self.TargetValues:
            return new_line

        # retractions are only F (feed rate) and E (extrude), at least in cura
        if x_coord is not None or y_coord is not None or z_coord is not None:
            return new_line

        # since retractions require both F and E, and we don't have either, we can't process
        if feed_rate is None or extrude_length is None:
            return new_line

        # get our desired retract feed rate
        retract_feed_rate = float(self.TargetValues["retractfeedrate"])

        # convert to units/min
        retract_feed_rate *= 60

        # replace our feed rate
        return GCodeCommand.replaceDirectArgument(new_line, "F", retract_feed_rate)

    # Used for finding settings in the print file before we process anything else
    def processSetting(self, line: str):

        # if we're in layers already we're out of settings
        if self.CurrentLayer is not None:
            return

        # check our retract length
        self.processRetractLengthSetting(line)

    # Sets the flags if we're at the target layer or not
    def processTargetLayer(self):

        # skip this line if we're not there yet
        if not self.isTargetLayerOrHeight():

            # flag that we're outside our target layer
            self.IsInsideTargetLayer = False

            # skip to the next line
            return

        # flip if we hit our target layer
        self.WasInsideTargetLayer = True

        # flag that we're inside our target layer
        self.IsInsideTargetLayer = True

    # Removes all the ChangeZ layer defaults from the given layer
    @staticmethod
    def removeMarkedChanges(layer: str) -> str:
        return re.sub(r";\[CAZD:DELETE:[\s\S]+?:CAZD\](\n|$)", "", layer)

    # Resets the class contents to defaults
    def reset(self):

        self.TargetValues = {}
        self.IsApplyToSingleLayer = False
        self.LastE = None
        self.CurrentZ = None
        self.CurrentLayer = None
        self.IsTargetByLayer = True
        self.TargetLayer = None
        self.TargetZ = None
        self.LayerHeight = None
        self.LastValues = {}
        self.IsLinearRetraction = True
        self.IsInsideTargetLayer = False
        self.IsTargetValuesInjected = False
        self.IsLastValuesRestored = False
        self.WasInsideTargetLayer = False
        self.IsEnabled = True

    # Sets the original GCODE line in a given GCODE command
    @staticmethod
    def setOriginalLine(line, original) -> str:
        return line + ";[CAZO:" + original + ":CAZO]"

    # Tracks the change in gcode values we're interested in
    def trackChangeableValues(self, line: str):

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

        # handle retract length changes
        if command.Command == "M207":

            # get our retract length if provided
            if "S" in command.Arguments:
                self.LastValues["retractlength"] = command.getArgumentAsFloat("S")

            # get our retract feedrate if provided, convert from mm/m to mm/s
            if "F" in command.Arguments:
                self.LastValues["retractfeedrate"] = command.getArgumentAsFloat("F") / 60.0

            # move to the next command
            return

        # handle bed temp changes
        if command.Command == "M140" or command.Command == "M190":

            # get our bed temp if provided
            if "S" in command.Arguments:
                self.LastValues["bedTemp"] = command.getArgumentAsFloat("S")

            # move to the next command
            return

        # handle extruder temp changes
        if command.Command == "M104" or command.Command == "M109":

            # get our tempurature
            tempurature = command.getArgumentAsFloat("S")

            # don't bother if we don't have a tempurature
            if tempurature is None:
                return

            # get our extruder, default to extruder one
            extruder = command.getArgumentAsInt("T", None)

            # set our extruder temp based on the extruder
            if extruder is None or extruder == 0:
                self.LastValues["extruderOne"] = tempurature

            if extruder is None or extruder == 1:
                self.LastValues["extruderTwo"] = tempurature

            # move to the next command
            return

        # handle fan speed changes
        if command.Command == "M106":

            # get our bed temp if provided
            if "S" in command.Arguments:
                self.LastValues["fanSpeed"] = (command.getArgumentAsInt("S") / 255.0) * 100

            # move to the next command
            return

        # handle flow rate changes
        if command.Command == "M221":

            # get our flow rate
            tempurature = command.getArgumentAsFloat("S")

            # don't bother if we don't have a flow rate (for some reason)
            if tempurature is None:
                return

            # get our extruder, default to global
            extruder = command.getArgumentAsInt("T", None)

            # set our extruder temp based on the extruder
            if extruder is None:
                self.LastValues["flowrate"] = tempurature
            elif extruder == 1:
                self.LastValues["flowrateOne"] = tempurature
            elif extruder == 1:
                self.LastValues["flowrateTwo"] = tempurature

            # move to the next command
            return

        # handle print speed changes
        if command.Command == "M220":

            # get our speed if provided
            if "S" in command.Arguments:
                self.LastValues["speed"] = command.getArgumentAsInt("S")

            # move to the next command
            return
