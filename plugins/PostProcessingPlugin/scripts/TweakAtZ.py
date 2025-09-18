"""
 TweakAtZ 2.0 is a re-write of ChangeAtZ by GregValiant (Greg Foresi) March 2025
    The script name change was required to avoid conflicts with project files that might use ChangeAtZ variables.
    Differences from the previous ChangeAtZ version (5.3.0):
        ~"By Height" will work with Z-hops enabled, Adaptive Layers, Scarf Z-seam, and Rafts.  The changes will commence at the first layer where the height is reached or exceeded.  The changes will end at the start of the layer where the End Height is reached or exceeded.
        ~The user can opt to change just the print speed or both print and travel speeds.  The 'F' parameters are re-calculated line-by-line using the percentage that the user inputs.  Speeds can now be changed 'per extruder'.  M220 is no longer used to change speeds as it affected all speeds.
        ~Changing the print speed no longer affects retraction or unretract speeds.
        ~The Z-hop speed is never affected.
        ~The 'Output to LCD' setting is obsolete to avoid flooding the screen with messages that were quickly over-written.
        ~Allows the user to select a Range of Layers (rather than just 'Single Layer' or 'To the End'.)
        ~Added support for control of a single fan.  This might be a Build Volume Fan, Auxilliary Fan, or a Layer Cooling Fan.  It would depend on the fan circuit number that the user inputs.
        ~Added support for Relative Extrusion
        ~Added support for Firmware Retraction
        ~Added support for 'G2' and 'G3' moves.
        ~The script supports a maximum of 2 extruders.
        ~'One-at-a-Time' is not supported and a kick-out is added

    Previous contributions by:
        Original Authors and contributors to the ChangeAtZ post-processing script and the earlier TweakAtZ:
            Written by Steven Morlock,
            Modified by Ricardo Gomez, to add Bed Temperature and make it work with Cura_13.06.04+
            Modified by Stefan Heule, since V3.0
            Modified by Jaime van Kessel (Ultimaker), to make it work for 15.10 / 2.x
            Modified by Ghostkeeper (Ultimaker), to debug.
            Modified by Wes Hanney, Retract Length + Speed, Clean up
            Modified by Alex Jaxon, Added option to modify Build Volume Temperature
            Re-write by GregValiant, to work with new variables in Cura 5.x and with the changes noted above
"""

from UM.Application import Application
from ..Script import Script
import re
from UM.Message import Message
from UM.Logger import Logger

class TweakAtZ(Script):
    version = "2.0.0"

    def initialize(self) -> None:
        """
        Prepare the script settings for the machine hardware configuration on Cura opening
        """
        super().initialize()
        self.global_stack = Application.getInstance().getGlobalContainerStack()
        self.extruder_count = int(self.global_stack.getProperty("machine_extruder_count", "value"))
        # If the printer is multi-extruder then enable the settings for T1
        if self.extruder_count == 1:
            self._instance.setProperty("multi_extruder", "value", False)
        else:
            self._instance.setProperty("multi_extruder", "value", True)

        # Enable the build volume temperature change when a heated build volume is present
        machine_heated_build_volume = bool(self.global_stack.getProperty("machine_heated_build_volume", "value"))
        if machine_heated_build_volume:
            self._instance.setProperty("heated_build_volume", "value", True)
        else:
            self._instance.setProperty("heated_build_volume", "value", False)

        # If it doesn't have a heated bed it is unlikely to have a Chamber or Auxiliary fan.
        has_heated_bed = bool(self.global_stack.getProperty("machine_heated_bed", "value"))
        if has_heated_bed:
            self._instance.setProperty("has_bv_fan", "value", True)

    def getSettingDataString(self):
        return """{
            "name": "Tweak At Z (2.0)",
            "key": "TweakAtZ",
            "metadata": {},
            "version": 2,
            "settings": {
                "taz_enabled": {
                    "label": "Enable Tweak at Z",
                    "description": "Enables the script so it will run.  You may have more than one instance of 'Tweak At Z' in the list of post processors.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "by_layer_or_height": {
                    "label": "'By Layer' or 'By Height'",
                    "description": "Which criteria to use to start and end the changes.",
                    "type": "enum",
                    "options":
                    {
                        "by_layer": "By Layer",
                        "by_height": "By Height"
                    },
                    "default_value": "by_layer",
                    "enabled": "taz_enabled"
                },
                "a_start_layer": {
                    "label": "Start Layer",
                    "description": "Layer number to start the changes at.  Use the Cura preview layer numbers.  The changes will start at the beginning of the layer.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": -7,
                    "minimum_value_warning": 1,
                    "unit": "Layer #",
                    "enabled": "taz_enabled and by_layer_or_height == 'by_layer'"
                },
                "a_end_layer": {
                    "label": "End Layer",
                    "description": "Use '-1' to indicate the end of the last layer.  The changes will end at the end of the indicated layer.  Use the Cura preview layer number.  If the 'Start Layer' is equal to the 'End Layer' then the changes only affect that single layer.",
                    "type": "int",
                    "default_value": -1,
                    "unit": "Layer #",
                    "enabled": "taz_enabled and by_layer_or_height == 'by_layer'"
                },
                "a_height_start": {
                    "label": "Height Start of Changes",
                    "description": "Enter the 'Z-Height' to Start the changes at.  The changes START at the beginning of the first layer where this height is reached (or exceeded).  If the model is on a raft then this height will be from the top of the air gap (first height of the actual model print).",
                    "type": "float",
                    "default_value": 0,
                    "unit": "mm",
                    "enabled": "taz_enabled and by_layer_or_height == 'by_height'"
                },
                "a_height_end": {
                    "label": "Height End of Changes",
                    "description": "Enter the 'Z-Height' to End the changes at.  The changes continue until this height is reached or exceeded.  If the model is on a raft then this height will be from the top of the air gap (first height of the actual model print).",
                    "type": "float",
                    "default_value": 0,
                    "unit": "mm",
                    "enabled": "taz_enabled and by_layer_or_height == 'by_height'"
                },
                "b_change_speed": {
                    "label": "Change Speeds",
                    "description": "Check to enable a speed change for the Print Speeds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "taz_enabled"
                },
                "change_speed_per_extruder": {
                    "label": "    Which extruder(s)",
                    "description": "For multi-extruder printers the changes can be for either or both extruders.",
                    "type": "enum",
                    "options": {
                        "ext_0": "Extruder 1 (T0)",
                        "ext_1": "Extruder 2 (T1)",
                        "ext_both": "Both extruders"},
                    "default_value": "ext_both",
                    "enabled": "taz_enabled and b_change_speed and multi_extruder"
                },
                "b_change_printspeed": {
                    "label": "    Include Travel Speeds",
                    "description": "Check this box to change the Travel Speeds as well as the Print Speeds.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "b_change_speed and taz_enabled"
                },
                "b_speed": {
                    "label": "    Speed %",
                    "description": "Speed factor as a percentage.  The chosen speeds will be altered by this much.",
                    "unit": "%  ",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 10,
                    "minimum_value_warning": 50,
                    "maximum_value_warning": 200,
                    "enabled": "b_change_speed and taz_enabled"
                },
                "c_change_flowrate": {
                    "label": "Change Flow Rate",
                    "description": "Select to change the flow rate of all extrusions in the layer range.  This command uses M221 to set the flow percentage in the printer.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "taz_enabled"
                },
                "c_flowrate_t0": {
                    "label": "    Flow Rate % (T0)",
                    "description": "Enter the new Flow Rate Percentage.  For a multi-extruder printer this will apply to Extruder 1 (T0).",
                    "unit": "%  ",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 25,
                    "minimum_value_warning": 50,
                    "maximum_value_warning": 150,
                    "maximum_value": 200,
                    "enabled": "c_change_flowrate and taz_enabled"
                },
                "multi_extruder": {
                    "label": "Hidden setting to enable 2nd extruder settings for multi-extruder printers.",
                    "description": "Enable T1 options.",
                    "type": "bool",
                    "value": false,
                    "default_value": false,
                    "enabled": false
                },
                "c_flowrate_t1": {
                    "label": "    Flow Rate % T1",
                    "description": "New Flow rate percentage for Extruder 2 (T1).",
                    "unit": "%  ",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 1,
                    "minimum_value_warning": 10,
                    "maximum_value_warning": 200,
                    "enabled": "multi_extruder and c_change_flowrate and taz_enabled"
                },
                "d_change_bed_temp": {
                    "label": "Change Bed Temp",
                    "description": "Select if Bed Temperature is to be changed.  The bed temperature will revert at the End Layer.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "taz_enabled"
                },
                "d_bedTemp": {
                    "label": "    Bed Temp",
                    "description": "New Bed Temperature",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 60,
                    "minimum_value": 0,
                    "minimum_value_warning": 30,
                    "maximum_value_warning": 120,
                    "enabled": "d_change_bed_temp and taz_enabled"
                },
                "heated_build_volume": {
                    "label": "Hidden setting",
                    "description": "This enables the build volume settings",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "e_change_build_volume_temperature": {
                    "label": "Change Build Volume Temperature",
                    "description": "Select if Build Volume Temperature is to be changed",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "heated_build_volume and taz_enabled"
                },
                "e_build_volume_temperature": {
                    "label": "    Build Volume Temperature",
                    "description": "New Build Volume Temperature.  This will revert at the end of the End Layer.",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 20,
                    "minimum_value": 0,
                    "minimum_value_warning": 15,
                    "maximum_value_warning": 80,
                    "enabled": "heated_build_volume and e_change_build_volume_temperature and taz_enabled"
                },
                "f_change_extruder_temperature": {
                    "label": "Change Print Temp",
                    "description": "Select if the Printing Temperature is to be changed",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "taz_enabled"
                },
                "f_extruder_temperature_t0": {
                    "label": "    Extruder 1 Temp (T0)",
                    "description": "New temperature for Extruder 1 (T0).",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 190,
                    "minimum_value": 0,
                    "minimum_value_warning": 160,
                    "maximum_value_warning": 250,
                    "enabled": "f_change_extruder_temperature and taz_enabled"
                },
                "f_extruder_temperature_t1": {
                    "label": "    Extruder 2 Temp (T1)",
                    "description": "New temperature for Extruder 2 (T1).",
                    "unit": "°C  ",
                    "type": "int",
                    "default_value": 190,
                    "minimum_value": 0,
                    "minimum_value_warning": 160,
                    "maximum_value_warning": 250,
                    "enabled": "multi_extruder and f_change_extruder_temperature and taz_enabled"
                },
                "g_change_retract": {
                    "label": "Change Retraction Settings",
                    "description": "Indicates you would like to modify retraction properties.  If 'Firmware Retraction' is enabled then M207 and M208 lines are added.  Your firmware must understand those commands.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "taz_enabled and not multi_extruder"
                },
                "g_change_retract_speed": {
                    "label": "    Change Retract/Prime Speed",
                    "description": "Changes the retraction and prime speed.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "g_change_retract and taz_enabled and not multi_extruder"
                },
                "g_retract_speed": {
                    "label": "        Retract/Prime Speed",
                    "description": "New Retract Feed Rate (mm/s).  If 'Firmware Retraction' is enabled then M207 and M208 are used to change the retract and prime speeds and the distance.  NOTE: the same speed will be used for both retract and prime.",
                    "unit": "mm/s  ",
                    "type": "float",
                    "default_value": 40,
                    "minimum_value": 1,
                    "minimum_value_warning": 0,
                    "maximum_value_warning": 100,
                    "enabled": "g_change_retract and g_change_retract_speed and taz_enabled and not multi_extruder"
                },
                "g_change_retract_amount": {
                    "label": "    Change Retraction Amount",
                    "description": "Changes the retraction length during print",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "g_change_retract and taz_enabled and not multi_extruder"
                },
                "g_retract_amount": {
                    "label": "        Retract Amount",
                    "description": "New Retraction Distance (mm).  If firmware retraction is used then M207 and M208 are used to change the retract and prime amount.",
                    "unit": "mm  ",
                    "type": "float",
                    "default_value": 6.5,
                    "minimum_value": 0,
                    "maximum_value_warning": 20,
                    "enabled": "g_change_retract and g_change_retract_amount and taz_enabled and not multi_extruder"
                },
                "enable_bv_fan_change": {
                    "label": "Chamber/Aux Fan Change",
                    "description": "Can alter the setting of a secondary fan when the printer is equipped with one.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "has_bv_fan and taz_enabled"
                },
                "e1_build_volume_fan_speed": {
                    "label": "    Chamber/Aux Fan Speed",
                    "description": "New Build Volume or Auxiliary Fan Speed.  This will reset to zero at the end of the 'End Layer'.",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "enabled": "has_bv_fan and enable_bv_fan_change and taz_enabled"
                },
                "bv_fan_nr": {
                    "label": "    Chamber/Aux Fan Number",
                    "description": "The circuit number of the Auxilliary or Chamber fan.  M106 will be used and the 'P' parameter (the fan number) will be the number entered here.",
                    "type": "int",
                    "unit": "#",
                    "default_value": 3,
                    "minimum_value": 0,
                    "enabled": "has_bv_fan and enable_bv_fan_change and taz_enabled"
                },
                "has_bv_fan": {
                    "label": "Hidden setting",
                    "description": "Enables the Build Volume/Auxiliary fan speed control when 'machine_heated_bed' is true.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        # Exit if the script isn't enabled
        if not bool(self.getSettingValueByKey("taz_enabled")):
            data[0] += ";  [Tweak at Z] is not enabled\n"
            Logger.log("i", "[Tweak at Z] is not enabled")
            return data

        # Message the user and exit if the print sequence is 'One at a Time'
        if self.global_stack.getProperty("print_sequence", "value") == "one_at_a_time":
            Message(title = "[Tweak at Z]", text = "One-at-a-Time mode is not supported.  The script will exit without making any changes.").show()
            data[0] += ";  [Tweak at Z] Did not run (One at a Time mode is not supported)\n"
            Logger.log("i", "TweakAtZ does not support 'One at a Time' mode")
            return data

        # Exit if the gcode has been previously post-processed.
        if ";POSTPROCESSED" in data[0]:
            return data

        # Pull some settings from Cura
        self.extruder_list = self.global_stack.extruderList
        self.firmware_retraction = bool(self.global_stack.getProperty("machine_firmware_retract", "value"))
        self.relative_extrusion = bool(self.global_stack.getProperty("relative_extrusion", "value"))
        self.initial_layer_height = self.global_stack.getProperty("layer_height_0", "value")
        self.heated_build_volume = bool(self.global_stack.getProperty("machine_heated_build_volume", "value"))
        self.heated_bed = bool(self.global_stack.getProperty("machine_heated_bed", "value"))
        self.retract_enabled = bool(self.extruder_list[0].getProperty("retraction_enable", "value"))
        self.orig_bed_temp = self.global_stack.getProperty("material_bed_temperature", "value")
        self.orig_bv_temp = self.global_stack.getProperty("build_volume_temperature", "value")
        self.z_hop_enabled = bool(self.extruder_list[0].getProperty("retraction_hop_enabled", "value"))
        self.raft_enabled = True if str(self.global_stack.getProperty("adhesion_type", "value")) == "raft" else False
        # The Start and end layer numbers are used when 'By Layer' is selected
        self.start_layer = self.getSettingValueByKey("a_start_layer") - 1
        end_layer = int(self.getSettingValueByKey("a_end_layer"))
        nbr_raft_layers = 0
        if self.raft_enabled:
            for layer in data:
                if ";LAYER:-" in layer:
                    nbr_raft_layers += 1
                if ";LAYER:0\n" in layer:
                    break

        # Adjust the start layer to account for any raft layers
        self.start_layer -= nbr_raft_layers

        # Find the indexes of the Start and End layers if 'By Layer'
        self.start_index = 0

        # When retraction is enabled it adds a single line item to the data list
        self.end_index = len(data) - 1 - int(self.retract_enabled)
        if self.getSettingValueByKey("by_layer_or_height") == "by_layer":
            for index, layer in enumerate(data):
                if ";LAYER:" + str(self.start_layer) + "\n" in layer:
                    self.start_index = index
                    break

            # If the changes continue to the top layer
            if end_layer == -1:
                if self.retract_enabled:
                    self.end_index = len(data) - 2
                else:
                    self.end_index = len(data) - 1

            # If the changes end below the top layer
            else:

                # Adjust the end layer from base1 numbering to base0 numbering
                end_layer -= 1

                # Adjust the End Layer if it is not the top layer and if bed adhesion is 'raft'
                end_layer -= nbr_raft_layers
                for index, layer in enumerate(data):
                    if ";LAYER:" + str(end_layer) + "\n" in layer:
                        self.end_index = index
                        break

        # The Start and End heights are used to find the Start and End indexes when changes are 'By Height'
        elif self.getSettingValueByKey("by_layer_or_height") == "by_height":
            start_height = float(self.getSettingValueByKey("a_height_start"))
            end_height = float(self.getSettingValueByKey("a_height_end"))
            # Get the By Height start and end indexes
            self.start_index = self._is_legal_z(data, start_height)
            self.end_index = self._is_legal_z(data, end_height) - 1

        # Exit if the Start Layer wasn't found
        if self.start_index == 0:
            Message(title = "[Tweak at Z]", text = "The 'Start Layer' is beyond the top of the print.  The script did not run.").show()
            Logger.log("w", "[Tweak at Z] The 'Start Layer' is beyond the top of the print.  The script did not run.")
            return data

        # Adjust the End Index if the End Index < Start Index (required for the script to make changes)
        if self.end_index < self.start_index:
            self.start_index = self.end_index
            Message(title = "[Tweak at Z]", text = "Check the Gcode.  Your 'Start Layer/Height' input is higher than the End Layer/Height input.  The Start Layer has been adjusted to equal the End Layer.").show()

        # Map settings to corresponding methods
        procedures = {
            "b_change_speed": self._change_speed,
            "c_change_flowrate": self._change_flow,
            "d_change_bed_temp": self._change_bed_temp,
            "e_change_build_volume_temperature": self._change_bv_temp,
            "f_change_extruder_temperature": self._change_hotend_temp,
            "g_change_retract": self._change_retract,
            "has_bv_fan": self._change_bv_fan_speed
        }

        # Run the selected procedures
        for setting, method in procedures.items():
            if self.getSettingValueByKey(setting):
                method(data)
        data = self._format_lines(data)
        return data

    def _change_speed(self, data:str)->str:
        """
        The actual speed will be a percentage of the Cura calculated 'F' values in the gcode.  The percentage can be different for each extruder.  Travel speeds can also be affected dependent on the user input.
        :params:
            speed_x: The speed percentage to use
            print_speed_only: Only change speeds with extrusions (but not retract or primes)
            target_extruder: For multi-extruder printers this is the active extruder
            off_extruder: For multi-extruders this is the inactive extruder.
        """
        # Since a single extruder changes all relevant speed settings then for a multi-extruder 'both extruders' is the same
        if self.extruder_count == 1 or self.getSettingValueByKey("change_speed_per_extruder") == "ext_both":
            speed_x = self.getSettingValueByKey("b_speed")/100
            print_speed_only = not bool(self.getSettingValueByKey("b_change_printspeed"))
            for index, layer in enumerate(data):
                if index >= self.start_index and index <= self.end_index:
                    lines = layer.splitlines()
                    for l_index, line in enumerate(lines):
                        if self._f_x_y_not_z(line):
                            f_value = self.getValue(line, "F")
                            if line.startswith(("G1", "G2", "G3")):
                                lines[l_index] = line.replace("F" + str(f_value), "F" + str(round(f_value * speed_x)))
                                lines[l_index] += f" ; TweakAtZ: {round(speed_x * 100)}% Print Speed"
                                continue
                            if not print_speed_only and line.startswith("G0"):
                                lines[l_index] = line.replace("F" + str(f_value), "F" + str(round(f_value * speed_x)))
                                lines[l_index] += f" ; TweakAtZ: {round(speed_x * 100)}% Travel Speed"
                    data[index] = "\n".join(lines) + "\n"
        elif self.extruder_count > 1:
            speed_x = self.getSettingValueByKey("b_speed")/100
            print_speed_only = not bool(self.getSettingValueByKey("b_change_printspeed"))
            target_extruder = self.getSettingValueByKey("change_speed_per_extruder")

            # These variables are used as the 'turn changes on' and 'turn changes off' at tool changes.
            if target_extruder == "ext_0":
                target_extruder = "T0"
                off_extruder = "T1"
            elif target_extruder == "ext_1":
                target_extruder = "T1"
                off_extruder = "T0"

            # After all of that it goes to work.
            for index, layer in enumerate(data):
                if index < self.start_index:
                    lineT = layer.splitlines()
                    for tline in lineT:
                        if "T0" in tline:
                            active_tool = "T0"
                        if "T1" in tline:
                            active_tool = "T1"
                if index >= self.start_index and index <= self.end_index:
                    lines = layer.splitlines()
                    for l_index, line in enumerate(lines):
                        if active_tool == target_extruder:
                            if self._f_x_y_not_z(line):
                                f_value = self.getValue(line, "F")
                                if line.startswith(("G1", "G2", "G3")):
                                    lines[l_index] = line.replace("F" + str(f_value), "F" + str(round(f_value * speed_x)))
                                    lines[l_index] += f" ; TweakAtZ: {round(speed_x * 100)}% Print Speed"
                                    continue
                                if not print_speed_only and line.startswith("G0"):
                                    lines[l_index] = line.replace("F" + str(f_value), "F" + str(round(f_value * speed_x)))
                                    lines[l_index] += f" ; TweakAtZ: {round(speed_x * 100)}% Travel Speed"
                        if line.startswith(off_extruder):
                            active_tool = off_extruder
                        if line.startswith(target_extruder):
                            active_tool = target_extruder

                    data[index] = "\n".join(lines) + "\n"
        return data

    def _change_flow(self, data:str)->str:
        """
        M221 is used to change the flow rate.
        :params:
            new_flow_ext_0: The flowrate percentage from these script settings (for the primary extruder)
            new_flowrate_0: The string to use for the new flowrate for T0
            reset_flowrate_0: Resets the flowrate to 100% (for either extruder)
            new_flow_ext_1: The flowrate percentage from these script settings (for the secondary extruder)
            new_flowrate_1: The string to use for the new flowrate for T1
        """
        new_flow_ext_0 = self.getSettingValueByKey("c_flowrate_t0")
        new_flowrate_0 = f"\nM221 S{new_flow_ext_0} ; TweakAtZ: Alter Flow Rate"
        reset_flowrate_0 = "\nM221 S100 ; TweakAtZ: Reset Flow Rate"
        if self.extruder_count > 1:
            new_flow_ext_1 = self.getSettingValueByKey("c_flowrate_t1")
            new_flowrate_1 = f"\nM221 S{new_flow_ext_1} ; TweakAtZ: Alter Flow Rate"
        else:
            new_flowrate_1 = ""

        # For single extruder
        if self.extruder_count == 1:
            lines = data[self.start_index].splitlines()
            lines[0] += new_flowrate_0
            data[self.start_index] = "\n".join(lines) + "\n"
            lines = data[self.end_index].splitlines()
            lines[len(lines) - 2] += reset_flowrate_0
            data[self.end_index] = "\n".join(lines) + "\n"

        # For dual-extruders
        elif self.extruder_count > 1:
            for index, layer in enumerate(data):
                if index < self.start_index:
                    continue
                else:
                    lines = layer.splitlines()
                    for l_index, line in enumerate(lines):
                        if line.startswith("T0"):
                            lines[l_index] += new_flowrate_0 + " T0"
                        if line.startswith("T1"):
                            lines[l_index] += new_flowrate_1 + " T1"
                    data[index] = "\n".join(lines) + "\n"
                    if index == self.end_index:
                        lines = data[index].splitlines()
                        lines[len(lines) - 2] += "\nM221 S100 ; TweakAtZ: Reset Flow Rate"
                        data[index] = "\n".join(lines) + "\n"
                        break
                if index > self.end_index:
                    break
        return data

    def _change_bed_temp(self, data:str)->str:
        """
        Change the Bed Temperature at height or layer
        :params:
        new_bed_temp: The new temperature from the settings for this script
        """
        if not self.heated_bed:
            return data
        new_bed_temp = self.getSettingValueByKey("d_bedTemp")
        if self.start_index == 2:
            if "M140 S" in data[2]:
                data[2] = re.sub("M140 S", ";M140 S", data[2])
            if "M140 S" in data[3]:
                data[3] = re.sub("M140 S", ";M140 S", data[3])
        lines = data[self.start_index].splitlines()
        lines[0] += "\nM140 S" + str(new_bed_temp) + " ; TweakAtZ: Change Bed Temperature"
        data[self.start_index] = "\n".join(lines) + "\n"
        lines = data[self.end_index].splitlines()
        lines[len(lines) - 2] += "\nM140 S" + str(self.orig_bed_temp) + " ; TweakAtZ: Reset Bed Temperature"
        data[self.end_index] = "\n".join(lines) + "\n"
        return data

    def _change_bv_temp(self, data:str)->str:
        """
        Change the Build Volume temperature at height or layer
        :param:
        new_bv_temp: The new temperature from the settings for this script
        """
        if not self.heated_build_volume:
            return data
        new_bv_temp = self.getSettingValueByKey("e_build_volume_temperature")
        lines = data[self.start_index].splitlines()
        lines[0] += "\nM141 S" + str(new_bv_temp) + " ; TweakAtZ: Change Build Volume Temperature"
        data[self.start_index] = "\n".join(lines) + "\n"
        lines = data[self.end_index].splitlines()
        lines[len(lines) - 2] += "\nM141 S" + str(self.orig_bv_temp) + " ; TweakAtZ: Reset Build Volume Temperature"
        data[self.end_index] = "\n".join(lines) + "\n"
        return data

    def _change_hotend_temp(self, data:str)->str:
        """
        Changes to the hot end temperature(s).
        :params:
            extruders_share_heater: Lets the script know how to handle the differences
            active_tool: Tracks the active tool through the gcode
            new_hotend_temp_0: The new temperature for the primary extruder T0
            orig_hot_end_temp_0: The print temperature for the primary extruder T0 as set in Cura
            orig_standby_temp_0: The standby temperature for the primary extruder T0 from Cura.  This marks a temperature line to ignore.
            new_hotend_temp_1: The new temperature for the secondary extruder T1
            orig_hot_end_temp_1: The print temperature for the secondary extruder T1 as set in Cura
            orig_standby_temp_1: The standby temperature for the secondary extruder T1 from Cura.  This marks a temperature line to ignore.
        """
        extruders_share_heater = bool(self.global_stack.getProperty("machine_extruders_share_heater", "value"))
        self.active_tool = "T0"
        self.new_hotend_temp_0 = self.getSettingValueByKey("f_extruder_temperature_t0")
        self.orig_hot_end_temp_0 = int(self.extruder_list[0].getProperty("material_print_temperature", "value"))
        self.orig_standby_temp_0 = int(self.extruder_list[0].getProperty("material_standby_temperature", "value"))

        # Start with single extruder machines
        if self.extruder_count == 1:
            if self.start_index == 2:
                if "M104 S" in data[2]:
                    data[2] = re.sub("M104 S", ";M104 S", data[2])
                if "M104 S" in data[3]:
                    data[3] = re.sub("M104 S", ";M104 S", data[3])

            # Add the temperature change at the beginning of the start layer
            lines = data[self.start_index].splitlines()
            for index, line in enumerate(lines):
                lines[0] += "\n" + "M104 S" + str(self.new_hotend_temp_0) + " ; TweakAtZ: Change Nozzle Temperature"
                data[self.start_index] = "\n".join(lines) + "\n"
                break

            # Revert the temperature to the Cura setting at the end of the end layer
            lines = data[self.end_index].splitlines()
            for index, line in enumerate(lines):
                lines[len(lines) - 2] += "\n" + "M104 S" + str(self.orig_hot_end_temp_0) + " ; TweakAtZ: Reset Nozzle Temperature"
                data[self.end_index] = "\n".join(lines) + "\n"
                break

        # Multi-extruder machines
        elif self.extruder_count > 1:
            self.new_hotend_temp_1 = self.getSettingValueByKey("f_extruder_temperature_t1")
            self.orig_hot_end_temp_1 = int(self.extruder_list[1].getProperty("material_print_temperature", "value"))
            self.orig_standby_temp_1 = int(self.extruder_list[1].getProperty("material_standby_temperature", "value"))

            # Track the tool number up to the start of the start layer
            self.getTool("T0")
            for index, layer in enumerate(data):
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith("T"):
                        self.getTool(line)
                if index == self.start_index - 1:
                    break

            # Add the active extruder initial temperature change at the start of the starting layer
            data[self.start_index] = data[self.start_index].replace("\n", f"\nM104 S{self.active_print_temp} ; TweakAtZ: Start Temperature Change\n",1)

            # At the start layer commence making the changes
            for index, layer in enumerate(data):
                if index < self.start_index:
                    continue
                if index > self.end_index:
                    break
                lines = layer.splitlines()
                for l_index, line in enumerate(lines):

                    # Continue to track the tool number
                    if line.startswith("T"):
                        self.getTool(line)
                    if line.startswith("M109"):
                        lines[l_index] = f"M109 S{self.active_print_temp} ; TweakAtZ: Alter temperature"
                    elif line.startswith("M104"):
                        if self.getValue(line, "S") == self.inactive_standby_temp:
                            continue
                        elif self.getValue(line, "S") == self.inactive_tool_orig_temp:
                            lines[l_index] = re.sub("S(\d+|\d.+)", f"S{self.inactive_print_temp} ; TweakAtZ: Alter temperature", line)
                        elif self.getValue(line, "S") == self.active_tool_orig_temp:
                            lines[l_index] = re.sub("S(\d+|\d.+)", f"S{self.active_print_temp} ; TweakAtZ: Alter temperature", line)
                data[index] = "\n".join(lines) + "\n"

            # Revert the active extruder temperature at the end of the changes
            lines = data[self.end_index].split("\n")
            lines[len(lines) - 3] += f"\nM104 {self.active_tool} S{self.active_tool_orig_temp} ; TweakAtZ: Original Temperature active tool"
            data[self.end_index] = "\n".join(lines)
        return data

    def getTool(self, line):
        if line.startswith("T1"):
            self.active_tool = "T1"
            self.active_tool_orig_temp = self.orig_hot_end_temp_1
            self.active_print_temp = self.new_hotend_temp_1
            self.inactive_tool = "T0"
            self.inactive_tool_orig_temp = self.orig_hot_end_temp_0
            self.inactive_print_temp = self.new_hotend_temp_0
            self.inactive_standby_temp = self.orig_standby_temp_0
        else:
            self.active_tool = "T0"
            self.active_tool_orig_temp = self.orig_hot_end_temp_0
            self.active_print_temp = self.new_hotend_temp_0
            self.inactive_tool = "T1"
            self.inactive_tool_orig_temp = self.orig_hot_end_temp_1
            self.inactive_print_temp = self.new_hotend_temp_1
            self.inactive_standby_temp = self.orig_standby_temp_1
        return

    def _change_retract(self, data:str)->str:
        """
        This is for single extruder printers only (tool change retractions get in the way for multi-extruders).
        Depending on the selected options, this will change the Retraction Speeds and Prime Speeds, and the Retraction Distance.  NOTE: The retraction and prime speeds will be the same.
        :params:
            speed_retract_0:  The set retraction and prime speed from Cura.
            retract_amt_0:  The set retraction distance from Cura
            change_retract_amt:  Boolean to trip changing the retraction distance
            change_retract_speed:  Boolean to trip changing the speeds
            new_retract_amt:  The new retraction amount to use from this script settings.
            new_retract_speed:  The new retract and prime speed from this script settings.
            firmware_start_str:  The string to insert for changes to firmware retraction
            firmware_reset:  The last insertion for firmware retraction will set the numbers back to the settings in Cura.
            is_retracted:  Tracks the end of the filament location
            cur_e:  The current location of the extruder
            prev_e:  The location of where the extruder was before the current e
        """
        if not self.retract_enabled:
            return

        # Exit if neither child setting is checked.
        if not (change_retract_amt or change_retract_speed):
            return

        speed_retract_0 = int(self.extruder_list[0].getProperty("retraction_speed", "value") * 60)
        retract_amt_0 = self.extruder_list[0].getProperty("retraction_amount", "value")
        change_retract_amt = self.getSettingValueByKey("g_change_retract_amount")
        change_retract_speed = self.getSettingValueByKey("g_change_retract_speed")
        new_retract_speed = int(self.getSettingValueByKey("g_retract_speed") * 60)
        new_retract_amt = self.getSettingValueByKey("g_retract_amount")

        # Use M207 and M208 to adjust firmware retraction when required
        if self.firmware_retraction:
            lines = data[self.start_index].splitlines()
            firmware_start_str = "\nM207"
            firmware_reset = ""
            if change_retract_speed:
                firmware_start_str += f" F{new_retract_speed}"
            if change_retract_amt:
                firmware_start_str += f" S{new_retract_amt}"
            if change_retract_speed or change_retract_amt:
                firmware_start_str += " ; TweakAtZ: Alter Firmware Retract speed/amt"
            if change_retract_speed:
                firmware_start_str += f"\nM208 F{new_retract_speed} ; TweakAtZ: Alter Firmware Prime speed"
            lines[0] += firmware_start_str
            data[self.start_index] = "\n".join(lines) + "\n"
            lines = data[self.end_index].splitlines()
            firmware_reset = f"M207 F{speed_retract_0} S{retract_amt_0} ; TweakAtZ: Reset Firmware Retract"
            if change_retract_speed:
                firmware_reset += f"\nM208 S{speed_retract_0} ; TweakAtZ: Reset Firmware Prime"
            if len(lines) < 2:
                lines.append(firmware_reset)
            else:
                lines[len(lines) - 2] += "\n" + firmware_reset
            data[self.end_index] = "\n".join(lines) + "\n"
            return data

        if not self.firmware_retraction:
            prev_e = 0
            cur_e = 0
            is_retracted = False
            for num in range(1, self.start_index - 1):
                lines = data[num].splitlines()
                for line in lines:
                    if " E" in line:
                        cur_e = self.getValue(line, "E")
                        prev_e = cur_e
            for num in range(self.start_index, self.end_index):
                lines = data[num].splitlines()
                for index, line in enumerate(lines):
                    if line == "G92 E0":
                        cur_e = 0
                        prev_e = 0
                        continue
                    if " E" in line and self.getValue(line, "E") is not None:
                        cur_e = self.getValue(line, "E")
                    if cur_e >= prev_e and " X" in line and " Y" in line:
                        prev_e = cur_e
                        is_retracted = False
                        continue
                    if " F" in line and " E" in line and not " X" in line and not " Z" in line:
                        cur_speed = self.getValue(line, "F")
                        if cur_e < prev_e:
                            is_retracted = True
                            new_e = prev_e - new_retract_amt
                            if not self.relative_extrusion:
                                if change_retract_amt:
                                    lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_e))
                                    prev_e = new_e
                                if change_retract_speed:
                                    lines[index] = lines[index].replace("F" + str(cur_speed), "F" + str(new_retract_speed))
                            elif self.relative_extrusion:
                                if change_retract_amt:
                                    lines[index] = lines[index].replace("E" + str(cur_e), "E-" + str(new_retract_amt))
                                    prev_e = 0
                                if change_retract_speed:
                                    lines[index] = lines[index].replace("F" + str(cur_speed), "F" + str(new_retract_speed))
                            lines[index] += " ; TweakAtZ: Alter retract"
                        else:

                            # Prime line
                            if change_retract_speed:
                                lines[index] = lines[index].replace("F" + str(cur_speed), "F" + str(new_retract_speed))
                                prev_e = cur_e
                            if self.relative_extrusion:
                                if change_retract_amt:
                                    lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_retract_amt))
                                prev_e = 0
                            lines[index] += " ; TweakAtZ: Alter retract"
                            is_retracted = False
                data[num] = "\n".join(lines) + "\n"

            # If the changes end before the last layer and the filament is retracted, then adjust the first prime of the next layer so it doesn't blob.
            if is_retracted and self.getSettingValueByKey("a_end_layer") != -1:
                layer = data[self.end_index]
                lines = layer.splitlines()
                for index, line in enumerate(lines):
                    if " X" in line and " Y" in line and " E" in line:
                        break
                    if " F" in line and " E" in line and not " X" in line and not " Z" in line:
                        cur_e = self.getValue(line, "E")
                        if not self.relative_extrusion:
                            new_e = prev_e + new_retract_amt
                            if change_retract_amt:
                                lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_e)) + " ; TweakAtZ: Alter retract"
                                break
                        elif self.relative_extrusion:
                            if change_retract_amt:
                                lines[index] = lines[index].replace("E" + str(cur_e), "E" + str(new_retract_amt)) + " ; TweakAtZ: Alter retract"
                                break
                data[self.end_index] = "\n".join(lines) + "\n"
        return data

    def _format_lines(self, temp_data: str) -> str:
        """
        This adds '-' as padding so the setting descriptions are more readable in the gcode
        """
        for l_index, layer in enumerate(temp_data):
            lines = layer.split("\n")
            for index, line in enumerate(lines):
                if "; TweakAtZ:" in line:
                    lines[index] = lines[index].split(";")[0] + ";" + ("-" * (40 - len(lines[index].split(";")[0]))) + lines[index].split(";")[1]
            temp_data[l_index] = "\n".join(lines)
        return temp_data

    def _change_bv_fan_speed(self, temp_data: str) -> str:
        """
        This can be used to control any fan.  Typically this would be an Auxilliary or Build Volume fan
        :params:
            bv_fan_nr:  The 'P' number of the fan
            bv_fan_speed:  The new speed for the fan
            orig_bv_fan_speed:  The reset speed.  This is currently always "0" as the fan speed may not exist in Cura, or the fan might be 'on-off' and not PWM controlled.
        """
        if not self.getSettingValueByKey("enable_bv_fan_change"):
            return temp_data
        bv_fan_nr = self.getSettingValueByKey("bv_fan_nr")
        bv_fan_speed = self.getSettingValueByKey("e1_build_volume_fan_speed")
        orig_bv_fan_speed = 0
        if bool(self.extruder_list[0].getProperty("machine_scale_fan_speed_zero_to_one", "value")):
            bv_fan_speed = round(bv_fan_speed * 0.01, 2)
            orig_bv_fan_speed = round(orig_bv_fan_speed * 0.01, 2)
        else:
            bv_fan_speed = round(bv_fan_speed * 2.55)
            orig_bv_fan_speed = round(orig_bv_fan_speed * 2.55)

        # Add the changes to the gcode
        for index, layer in enumerate(temp_data):
            if index == self.start_index:
                lines = layer.split("\n")
                lines.insert(1, f"M106 S{bv_fan_speed} P{bv_fan_nr} ; TweakAtZ: Change Build Volume Fan Speed")
                temp_data[index] = "\n".join(lines)
            if index == self.end_index:
                lines = layer.split("\n")
                lines.insert(len(lines) - 2, f"M106 S{orig_bv_fan_speed} P{bv_fan_nr} ; TweakAtZ: Reset Build Volume Fan Speed")
                temp_data[index] = "\n".join(lines)
        return temp_data

    # Get the starting index or ending index of the change range when 'By Height'
    def _is_legal_z(self, data: str, the_height: float) -> int:
        """
        When in 'By Height' mode, this will return the index of the layer where the working Z is >= the Starting Z height, or the index of the layer where the working Z >= the Ending Z height
        :params:
            max_z:  The maximum Z height within the Gcode.  This is used to determine the upper limit of the data list that should be returned.
            the_height:  The user input height.  This will be adjusted if rafts are enabled and/or Z-hops are enabled
            cur_z:  Is the current Z height as tracked through the gcode
            the_index:  The number to return.
        """
        # The height passed down cannot exceed the height of the model or the search for the Z fails
        lines = data[0].split("\n")
        for line in lines:
            if "MAXZ" in line or "MAX.Z" in line:
                max_z = float(line.split(":")[1])
                break
        if the_height > max_z:
            the_height = max_z

        starting_z = 0
        the_index = 0

        # The start height varies depending whether or not rafts are enabled and whether Z-hops are enabled.
        if str(self.global_stack.getProperty("adhesion_type", "value")) == "raft":

            # If z-hops are enabled then start looking for the working Z after layer:0
            if self.z_hop_enabled:
                for layer in data:
                    if ";LAYER:0" in layer:
                        lines = layer.splitlines()
                        for index, line in enumerate(lines):
                            try:
                                if " Z" in line and " E" in lines[index + 1]:
                                    starting_z = round(float(self.getValue(line, "Z")),2)
                                    the_height += starting_z
                                    break

                            # If the layer ends without an extruder move following the Z line, then just jump out
                            except IndexError:
                                starting_z = round(float(self.getValue(line, "Z")),2)
                                the_height += starting_z
                                break

            # If Z-hops are disabled, then look for the starting Z from the start of the raft up to Layer:0
            else:
                for layer in data:
                    lines = layer.splitlines()
                    for index, line in enumerate(lines):

                        # This try/except catches comments in the startup gcode
                        try:
                            if " Z" in line and " E" in lines[index - 1]:
                                starting_z = float(self.getValue(line, "Z"))
                        except TypeError:

                            # Just pass beause there will be further Z values
                            pass
                        if ";LAYER:0" in line:
                            the_height += starting_z
                            break

        # Initialize 'cur_z'
        cur_z = self.initial_layer_height
        for index, layer in enumerate(data):

            # Skip over the opening paragraph and StartUp Gcode
            if index < 2:
                continue
            lines = layer.splitlines()
            for z_index, line in enumerate(lines):
                if len(line) >= 3 and line[0:3] in ['G0 ', 'G1 ', 'G2 ', 'G3 '] and index <= self.end_index:
                    if " Z" in line:
                        cur_z = float(self.getValue(line, "Z"))
                    if cur_z >= the_height and lines[z_index - 1].startswith(";TYPE:"):
                        the_index = index
                        break
            if the_index > 0:
                break

        # Catch-all to insure an entry of the 'model_height'.  This allows the changes to continue to the end of the top layer
        if the_height >= max_z:
            the_index = len(data) - 2
        return the_index

    def _f_x_y_not_z(self, line):
        return " F" in line and " X" in line and " Y" in line and not " Z" in line
