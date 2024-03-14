# By GregValiant (Greg Foresi) November 2023
# This script allows the users of single extruder printers to print Support-Interface with a second material.  It adds filament change pauses (to the selected layers) before and after any 'Support-Interface' sections within the layer.  Be advised that there can be a lot of filament changing going on as there are two pauses for each Interface on each affected layer.  Check your gcode to insure it is correct.  Searching the gcode for 'custom' will find the pauses.
#  This script works really well with large flat interfaces.  Because horizontal holes have limited contact with the support on any individual layer there can be a lot of pauses and the value of this script falls off as the annoyance factor goes up.
#  I tried printing a TPU model with both PLA as the interface and PETG as the interface.  TPU seems to stick well to both of them so the testing failed.

# RULES:
##   If insufficient material is purged, then the two materials may mix for the first few cm's of model extrusion.  That will affect the layer adhesion for that portion of the print.  It will also affect the color as the interface material might not be the same color as the print material.
##   Rafts are allowed.  Set the raft "Air Gap" to 0.0 and the Support Bottom Distance to 0.0.  If you try to use this script on the 2 topmost layers of a raft you will get back-to-back filament changes because rafts take up the entire layer and jumping between layers in post process isn't really allowed.  Using a second material for only the top raft layer works well.
##   If this script is used on the bottom interface then you can set the bottom distance to 0.  When used on a top interface the interface density should be 100% and the "Top Distance" 0.
##   Multi-extruder printers are allowed but may only have a single extruder enabled (tool change retractions are a problem).
##   The layer numbers you enter are the only ones searched for "TYPE:SUPPORT-INTERFACE" so be accurate when you pick the "layers of interest".  Checking the output gcode is a really good idea.
<<<<<<< HEAD
##
=======
##   
>>>>>>> 028430ac44a5bc07dd0f6e40abfadfc42915d3db
##   My normal setup is for the top two interface layers at 100% density and 0 air gap.  75mm of purge seems to be a sufficient for PLA and PETG.  If you purge then there will be a beep and a 2 second wait before the print resumes.  That allows you to grab the string.  My Ender 3 Pro is a bowden printer and 470mm of unload and 370mm of reload works well.  Yours will vary according to the length of the filament path from the extruder to the hot end.


from ..Script import Script
from cura.CuraApplication import CuraApplication
from UM.Message import Message
import re

class SuptIntMaterialChange(Script):

    def initialize(self) -> None:
        super().initialize()
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        ext_count = int(mycura.getProperty("machine_extruder_count", "value"))
        machine_width = int(mycura.getProperty("machine_width", "value"))
        self._instance.setProperty("park_x", "maximum_value", machine_width)
        machine_depth = int(mycura.getProperty("machine_depth", "value"))
        self._instance.setProperty("park_y", "maximum_value", machine_depth)
        self._instance.setProperty("model_temp", "value", extruder[0].getProperty("material_print_temperature", "value"))
        self._instance.setProperty("extra_prime_amt", "value", extruder[0].getProperty("retraction_amount", "value"))

        if ext_count > 1:
            Message(title = "[Supt-Interface Material Change]", text = "Only a single extruder can be enabled in order to use this post processor.  The post processor will exit if more than a single extruder is enabled because tool change retractions interfere.").show()
            return
        if str(mycura.getProperty("adhesion_type", "value")) == "raft":
            Message(title = "[Supt-Interface Material Change]", text = "When using a raft set the Raft Air Gap to 0.  Use the layer numbers in the Cura preview and the script will make the adjustments.").show()

    def getSettingDataString(self):
            return """{
            "name": "Support Interface Mat'l Change",
            "key": "SuptIntMaterialChange",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_method":
                {
                    "label": "Pause Command",
                    "description": "The gcode command to use to pause the print.  This is firmware dependent.  'M0 w/message(Marlin)' may show the LCD message if there is one.  'M0 (Marlin)' is the plain 'M0' command",
                    "type": "enum",
                    "options": {
                    "marlin": "M0 w/message(Marlin)",
                    "marlin2": "M0 (Marlin)",
                    "griffin": "M0 (Griffin,firmware retract)",
                    "bq": "M25 (BQ)",
                    "reprap": "M226 (RepRap)",
                    "repetier": "@pause (Repet/Octo)",
                    "alt_octo": "M125 (alt Octo)",
                    "raise_3d": "M2000 (raise3D)",
                    "klipper": "PAUSE (Klipper)",
                    "g_4": "G4 (dwell)",
                    "custom": "Custom Command"},
                    "default_value": "marlin",
                    "enabled": true
                },
                "g4_dwell_time":
                {
                    "label": "    G4 dwell time (in minutes)",
                    "description": "The amount of time to pause for. 'G4 S' is a 'hard' number.  You cannot make it shorter at the printer.  At the end of the dwell time - the printer will restart by itself.",
                    "type": "float",
                    "default_value": 5.0,
                    "minimum_value": 0.5,
                    "maximum_value_warning": 30.0,
                    "unit": "minutes   ",
                    "enabled": "pause_method == 'g_4'"
                },
<<<<<<< HEAD
                "gcode_after_pause":
                {
                    "label": "    Gcode after pause",
                    "description": "Some printers require a buffer after the pause when M25 is used. Typically 6 M105's works well.  Delimit multiple commands with a comma EX: M105,M105,M105",
                    "type": "str",
                    "default_value": "M105,M105,M105,M105,M105,M105",
                    "enabled": "pause_method not in ['marlin','marlin2','griffin','g_4']"
                },
=======
>>>>>>> 028430ac44a5bc07dd0f6e40abfadfc42915d3db
                "custom_pause_command":
                {
                    "label": "    Enter your pause command",
                    "description": "If none of the the stock options work with your printer you can enter a custom command here.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "pause_method == 'custom'"
                },
                "layers_of_interest":
                {
                    "label": "Layers #'s for Mat'l Change",
                    "description": "Use the Cura preview layer numbers.  Enter the layer numbers that you want to change material for the support interfaces.  The numbers must be ascending.  Delimit individual layer numbers with a ',' comma and delimit layer ranges with a '-' dash.  Spaces are not allowed.  If there is no 'SUPPORT-INTERFACE' on a layer then it is ignored.",
                    "type": "str",
                    "default_value": "10,15,28-31",
                    "enabled": true
                },
                "model_str":
                {
                    "label": "Model Mat'l (Msg to LCD)",
                    "description": "Message to appear on the LCD for the filament change.",
                    "type": "str",
                    "default_value": "PLA",
                    "enabled": true
                },
                "model_temp":
                {
                    "label": "     Model print temperature",
                    "description": "The temperature to use during the pause and for the filament being used to print the model.",
                    "type": "int",
                    "value": 205,
                    "default_value": 205,
                    "enabled": true
                },
                "interface_str":
                {
                    "label": "Interface Mat'l (Msg to LCD)",
                    "description": "Message to appear on the LCD for the filament change.",
                    "type": "str",
                    "default_value": "PETG",
                    "enabled": true
                },
                "interface_temp":
                {
                    "label": "     Interface mat'l print temp",
                    "description": "The temperature to use during the pause and for the support-interface material.",
                    "type": "int",
                    "value": 235,
                    "default_value": 235,
                    "enabled": true
                },
                "interface_flow":
                {
                    "label": "     Interface Flow Rate",
                    "description": "The percent flow rate of the support-interface material.  This will usually be 100% but can be tweaked here.  NOTE: At the end of each switch to the model material this script always sets the flow rate to 100%.  If you have other M220 lines in the gcode they will be negated by the M220 S100 lines.",
                    "type": "int",
                    "value": 100,
                    "unit": "%  ",
                    "default_value": 100,
                    "minimum_value": 50,
                    "maximum_value": 150,
                    "enabled": true
                },
                "unload_dist":
                {
                    "label": "Unload Filament Amount",
                    "description": "Enter a positive number or set this to 0 to disable.  This is the amount of filament to pull back after parking the head.",
                    "type": "int",
                    "unit": "mm  ",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 800,
                    "enabled": true
                },
                "load_dist":
                {
                    "label": "Load Filament Amount",
                    "description": "Enter a positive number or set this to 0 to disable.  This is the amount of filament to push after the pause.  90% of this distance will be fast and the last 10% slow so the extruder doesn't lose steps.",
                    "unit": "mm  ",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 800,
                    "enabled": true
                },
                "enable_purge":
                {
                    "label": "Enable Purge After Each Change",
                    "description": "Enable a filament purge before resuming the print.  Not purging can have side-effects.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "purge_amt_model":
                {
                    "label": "    Model Matl Purge Amt",
                    "description": "How much MODEL filament to purge before printing the INTERFACE.  If the amount is too little then the adhesion to the interface will be greater as the model material will mix with the interface material until it clears it out.  Purge occurs at the park position.",
                    "type": "int",
                    "default_value": 75,
                    "maximum_value": 150,
                    "minimum_value": 10,
                    "unit": "mm  ",
                    "enabled": "enable_purge"
                },
                "purge_amt_interface":
                {
                    "label": "    Interface Matl Purge Amt",
                    "description": "How much INTERFACE filament to purge before resuming the MODEL.  If the amount is too little then layer adhesion will suffer for the first couple of layers until the interface material clears out.  Purge occurs at the park position.",
                    "type": "int",
                    "default_value": 75,
                    "maximum_value": 150,
                    "minimum_value": 10,
                    "unit": "mm  ",
                    "enabled": "enable_purge"
                },
                "park_head":
                {
                    "label": "Park Head for changes?",
                    "description": "Whether to park the head when changing filament. The park position is the same for all pauses.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "park_x":
                {
                    "label": "    Park X",
                    "description": "The X location to park the head for all pauses.",
                    "type": "int",
                    "default_value": 0,
                    "maximum_value": 500,
                    "enabled": "park_head"
                },
                "park_y":
                {
                    "label": "    Park Y",
                    "description": "The Y location to park the head for all pauses.",
                    "type": "int",
                    "default_value": 0,
                    "maximum_value": 500,
                    "enabled": "park_head"
                },
                "m300_add":
                {
                    "label": "Beep at Pauses",
                    "description": "Add M300 line to beep at each pause.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "pause_method != 'm600fil_change'"
                },
                "m118_add":
                {
                    "label": "Add M118",
                    "description": "M118 bounces the M117 messages over the USB to a print server (like Pronterface or Octoprint).",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                }
            }
        }"""

    def execute(self, data):
        mycura = CuraApplication.getInstance().getGlobalContainerStack()
        extruder = mycura.extruderList
        ext_count = int(mycura.getProperty("machine_extruder_count", "value"))
        # Exit if the printer is a multi-extruder and more than 1 tool is enabled
        ext_enabled = 0
        if ext_count > 1:
            enabled_list = list([mycura.isEnabled for mycura in mycura.extruderList])
            for num in range(0,len(enabled_list)):
                if bool(enabled_list[num]):
                    ext_enabled += 1
        if ext_enabled > 1:
            Message(title = "[Supt-Interface Material Change]", text = "Is not compatible with more than a single enabled extruder.").show()
            data[0] += ";  [Supt-Interface Material Change] Did not run because more than one extruder is enabled.\n"
            return data

        # Count the raft layers
        raft_layers = 0
        if str(mycura.getProperty("adhesion_type", "value")) == "raft":
            for num in range(2,10,1):
                layer = data[num]
                if ";LAYER:-" in layer:
                    raft_layers += 1
                if ":LAYER:0\n" in layer:
                    break

        # Make a list of the user entered layer numbers
        layers_of_interest = str(self.getSettingValueByKey("layers_of_interest"))
        layer_list = []
        if "," in layers_of_interest:   # Start with the comma delimited layers
            the_layers = layers_of_interest.split(",")
            for layer in the_layers:
                if not "-" in layer:
                    layer_list.append(int(layer) - 1 - raft_layers)
                else:
                    startat = int(layer.split("-")[0])  # If there are layer ranges then split them and add all the layers to the list
                    endat = int(layer.split("-")[1])
                    for m in range(startat, endat + 1):
                        layer_list.append(m - 1 - raft_layers)
        elif "-" in layers_of_interest and not "," in layers_of_interest: # If there are no commas but there is a layer range
            startat = int(layers_of_interest.split("-")[0])
            endat = int(layers_of_interest.split("-")[1])
            for m in range(startat, endat + 1):
                layer_list.append(m - 1 - raft_layers)
        else:
            layer_list.append(int(layers_of_interest) - 1 - raft_layers)  # If there is a single layer entered
        ## Convert the Layer_List layer numbers to a Data_List of the corresponding data items.  That takes care of the any raft negative numbers.
        data_list = []
        for num in range(0,len(layer_list)):
            the_layer = int(layer_list[num])
            for data_num in range(the_layer, len(data)-1):
                if ";LAYER:" + str(the_layer) + "\n" in data[data_num]:
                    data_list.append(data_num)
                    break

        ## Check the Raft Air Gap.  If it is greater than 0 send a message.
        if raft_layers > 0:
            raft_airgap = mycura.getProperty("raft_airgap", "value")
            raft_is_included = True if layer_list[0] < 0 else False
            if raft_airgap > 0 and raft_is_included:
                Message(title = "[Supt-Interface Material Change]", text = "Your 'Raft Air Gap' is not 0.  This will work, but the bottom layer of the model is better if the air gap is 0.").show()

        ## Purging needs room under the nozzle so establish a minimum lift height of 25mm until the print is 25mm tall
        layer_height = mycura.getProperty("layer_height", "value")
        layer_height_0 = mycura.getProperty("layer_height_0", "value")
        z_lift_list = []
        for num in range(0,len(layer_list)):
            the_layer = int(layer_list[num])
            z_lift = layer_height_0 + (layer_height * the_layer)
            if z_lift < 25:
                z_lift = 25
            else:
                z_lift = 3
            z_lift_list.append(z_lift)

        ## Retrieve some settings from Cura and set up some variables
        m84_line = "M84 S3600; Keep steppers enabled for 1 hour"
        firmware_retraction = bool(mycura.getProperty("machine_firmware_retract", "value"))
        speed_travel = str(extruder[0].getProperty("speed_travel", "value") * 60)
        retract_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        retract_dist = str(extruder[0].getProperty("retraction_amount", "value"))
        retract_speed = str(extruder[0].getProperty("retraction_retract_speed", "value") * 60)
        unretract_speed = str(extruder[0].getProperty("retraction_prime_speed", "value") * 60)
        max_speed_e = str(mycura.getProperty("machine_max_feedrate_e", "value"))
        model_str = self.getSettingValueByKey("model_str")
        interface_str = self.getSettingValueByKey("interface_str")
        unload_reload_speed = int(mycura.getProperty("machine_max_feedrate_e", "value") * 60)
        if unload_reload_speed > 3000:
            unload_reload_speed = 3000
        enable_purge = bool(self.getSettingValueByKey("enable_purge"))
        purge_amt_model = int(self.getSettingValueByKey("purge_amt_model"))
        purge_amt_interface = int(self.getSettingValueByKey("purge_amt_interface"))

        ## Absolute or Relative Extrusion
        relative_ext_mode = bool(mycura.getProperty("relative_extrusion", "value"))
        if relative_ext_mode:
            ext_mode_str = "M83; Relative extrusion\n"
        else:
            ext_mode_str = "M82; Absolute extrusion\n"

        ## Retractions
        retract_line = ""
        unretract_line = ""
        if not firmware_retraction:
            if retract_enabled:
                retract_line = f"G1 F{retract_speed} E-{retract_dist}; Retract\n"
                unretract_line = f"G1 F{unretract_speed} E{retract_dist}; Unretract\n"
        else:
            if retract_enabled:
                retract_line = "G10; Retract\n"
                unretract_line = "G11; Unretract\n"

        ## Pause command
        g4_dwell_time = round(self.getSettingValueByKey("g4_dwell_time") * 60)
        pause_method = self.getSettingValueByKey("pause_method")
        if pause_method == "custom":
            custom_pause_command = self.getSettingValueByKey("custom_pause_command")
        else:
            custom_pause_command = ""
        pause_cmd_model = {
            "marlin": "M0 ",
            "marlin2": "M0",
            "griffin": self.putValue(M = 0),
            "bq": self.putValue(M = 25),
            "reprap": self.putValue(M = 226),
            "repetier": self.putValue("@pause now change filament and press continue printing"),
            "alt_octo": self.putValue(M = 125),
            "raise_3d": self.putValue(M = 2000),
            "klipper": self.putValue("PAUSE"),
            "custom": self.putValue(str(custom_pause_command)),
            "g_4": self.putValue(G = 4, S = g4_dwell_time)}[pause_method]
        ## M0 can overwrite the M117 message so add it to the M0 line if Marlin is chosen.  Add a comment and newline if it is other than Marlin.
        if pause_method == "marlin":
            pause_cmd_interface = pause_cmd_model + interface_str + " Click to Resume; Pause\n"
            pause_cmd_model += model_str + " Click to Resume; Pause\n"
        else:
            pause_cmd_model += "; Pause\n"
            pause_cmd_interface = pause_cmd_model

<<<<<<< HEAD
        ##Gcode after pause
        gcode_after_pause = ""
        if pause_method not in ["marlin","marlin2","griffin","g_4"]:
            gcode_after_pause = self.getSettingValueByKey("gcode_after_pause").upper()
            if gcode_after_pause != "":
                if "," in gcode_after_pause:
                    gcode_after_pause = re.sub(",", "; gcode after\n", gcode_after_pause)
                gcode_after_pause += "; gcode after\n"

=======
>>>>>>> 028430ac44a5bc07dd0f6e40abfadfc42915d3db
        ## Park Head
        park_head = self.getSettingValueByKey("park_head")
        park_x = self.getSettingValueByKey("park_x")
        park_y = self.getSettingValueByKey("park_y")
        if park_head:
            park_str = f"G0 F{round(float(speed_travel))} X{park_x} Y{park_y}; Move to park position\n"
        else:
            park_str = ""

        ## Buzzer
        if self.getSettingValueByKey("m300_add"):
            m300_str = "M300 S400 P1000; Beep\n"
        else:
            m300_str = ""

        ## Messages to the LCD
        model_str = "M117 " + str(self.getSettingValueByKey("model_str")) + "; Message to LCD\n"
        interface_str = "M117 " + str(self.getSettingValueByKey("interface_str")) + "; Message to LCD\n"
        m118_add = bool(self.getSettingValueByKey("m118_add"))
        if m118_add:
            m118_model_str = "M118 " + str(self.getSettingValueByKey("model_str")) + " at " + str(self.getSettingValueByKey("model_temp")) + "°" + "; Message to print server\n"
            m118_interface_str = "M118 " + str(self.getSettingValueByKey("interface_str")) + " at " + str(self.getSettingValueByKey("interface_temp")) + "°" + "; Message to print server\n"
        else:
            m118_model_str = ""
            m118_interface_str = ""

        ## Temperature lines
        interface_temp = int(self.getSettingValueByKey("interface_temp"))
        model_temp = int(self.getSettingValueByKey("model_temp"))
        if interface_temp > model_temp:
            median_temp = ((interface_temp - model_temp) / 2) + model_temp
        elif model_temp > interface_temp:
            median_temp = ((model_temp - interface_temp) / 2) + interface_temp
        else:
            median_temp = model_temp
        median_temp = "M104 S" + str(median_temp) + "; Median temperature during pause\n"
        interface_temp = "M109 R" + str(self.getSettingValueByKey("interface_temp")) + "; Interface material temperature\n"
        model_temp = "M109 R" + str(self.getSettingValueByKey("model_temp")) + "; Print material temperature\n"

        ## Flow lines
        flow_rate = str(self.getSettingValueByKey("interface_flow"))
        flow_rate_str = f"M221 S{flow_rate}        ; Set interface flow\n"
        flow_rate_reset = "M221 S100; Reset flow rate\n"

        ## Load and Unload lines
        if self.getSettingValueByKey("unload_dist") != 0:
            unload_dist = self.getSettingValueByKey("unload_dist")
            unload_str = self.getUnloadReloadScript(data, unload_dist, unload_reload_speed, retract_speed, True, retract_dist)
        else:
            unload_str = ""
        if self.getSettingValueByKey("load_dist") != 0:
            load_dist = self.getSettingValueByKey("load_dist")
            load_str = self.getUnloadReloadScript(data, load_dist, unload_reload_speed, unretract_speed, False, retract_dist)
        else:
            load_str = ""

        ## Purge Lines
        purge_str_model = ""
        if purge_amt_model > 0 and enable_purge:
            nozzle_size = CuraApplication.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_nozzle_size", "value")
            retraction_amount = CuraApplication.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_nozzle_size", "value")
            firmware_retract = bool(CuraApplication.getInstance().getGlobalContainerStack().getProperty("machine_firmware_retract", "value"))
            purge_str_model = "M83; Relative extrusion\n"
            purge_str_model += "G1 F" + str(round(float(nozzle_size) * 8.333) * 60) + " E" + str(purge_amt_model) + "; Purge\n"
            if not firmware_retract:
                purge_str_model += "G1 F" + str(int(retract_speed)) + " E-" + str(retract_dist) + "; Retract\n"
            else:
                purge_str_model += "G10; Retract\n"
            purge_str_model += "M400; Complete all moves\n"
            purge_str_model += "M300 P250; Beep\n"
            purge_str_model += "G4 S2; Wait for 2 seconds\n"

        purge_str_interface = ""
        if purge_amt_interface > 0 and enable_purge:
            nozzle_size = CuraApplication.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_nozzle_size", "value")
            retraction_amount = CuraApplication.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_nozzle_size", "value")
            firmware_retract = bool(CuraApplication.getInstance().getGlobalContainerStack().getProperty("machine_firmware_retract", "value"))
            purge_str_interface = "M83; Relative extrusion\n"
            purge_str_interface += "G1 F" + str(round(float(nozzle_size) * 8.333) * 60) + " E" + str(purge_amt_interface) + "; Purge\n"
            if not firmware_retract:
                purge_str_interface += "G1 F" + str(int(retract_speed)) + " E-" + str(retract_dist) + "; Retract\n"
            else:
                purge_str_interface += "G10; Retract\n"
            purge_str_interface += "M400; Complete all moves\n"
            purge_str_interface += "M300 P250; Beep\n"
            purge_str_interface += "G4 S2; Wait for 2 seconds\n"

        ## Put together the preliminary strings for the interface material and model material
        interface_replacement_pre_string_1 = ";TYPE:CUSTOM" + str('-' * 15) + "; Supt-Interface Material Change - Change to Interface Material" + "\n" + m84_line + "\nG91; Relative movement\nM83; Relative extrusion\n"
<<<<<<< HEAD
        interface_replacement_pre_string_2 = "G90; Absolute movement" + "\n" + park_str + m300_str + unload_str + interface_str + m118_interface_str + median_temp + pause_cmd_interface + gcode_after_pause + interface_temp
        model_replacement_pre_string_1 = ";TYPE:CUSTOM" + str('-' * 15) + "; Supt-Interface Material Change - Revert to Model Material" + "\n" + m84_line + "\n" + "G91; Relative movement" + "\nM83; Relative extrusion\n"
        model_replacement_pre_string_2 = "G90; Absolute movement" + "\n" + park_str + m300_str + unload_str + model_str + m118_model_str + median_temp + pause_cmd_model + gcode_after_pause + model_temp
=======
        interface_replacement_pre_string_2 = "G90; Absolute movement" + "\n" + park_str + m300_str + unload_str + interface_str + m118_interface_str + median_temp + pause_cmd_interface + interface_temp
        model_replacement_pre_string_1 = ";TYPE:CUSTOM" + str('-' * 15) + "; Supt-Interface Material Change - Revert to Model Material" + "\n" + m84_line + "\n" + "G91; Relative movement" + "\nM83; Relative extrusion\n"
        model_replacement_pre_string_2 = "G90; Absolute movement" + "\n" + park_str + m300_str + unload_str + model_str + m118_model_str + median_temp + pause_cmd_model + model_temp
>>>>>>> 028430ac44a5bc07dd0f6e40abfadfc42915d3db

        # Go through the relevant layers and add the strings
        for lnum in range(0,len(data_list)):
            index_list = []
            dnum = data_list[lnum]
            z_raise = f"G0 F2400 Z{z_lift_list[lnum]}; Move up\n"
            z_lower = f"G0 F2400 Z-{z_lift_list[lnum]}; Move back down\n"
            lines = data[dnum].split("\n")
            for index, line in enumerate(lines):
                if ";TYPE:SUPPORT-INTERFACE" in line:
                    index_list.append(index)
                    for check in range(index + 1, len(lines), 1):
                        if lines[check].startswith(";"):
                            index_list.append(check)
                            break
            ## Make a list of the starts and stops within a layer
            for index_num in range(0, len(index_list), 2):
                start_at_line = index_list[index_num]
                end_at_line = index_list[index_num + 1]
                ## Put the 'Revert' section together
                return_location_list = []
                return_location_list = self.getReturnLocation(data, dnum, end_at_line, retract_speed)
                return_location = str(return_location_list[0])
                is_retraction = bool(return_location_list[1])
                ## Relative extrusion or not
                if not relative_ext_mode:
                    return_e_reset_str = "G92 E" + str(return_location_list[2]) + "; Reset extruder\n"
                else:
                    return_e_reset_str = "G92 E0; Reset extruder\n"
                ## If there is a retraction prior to the Support Interface don't double dip
                if is_retraction:
                    retract_str = ""
                    unretract_str = ""
                else:
                    retract_str = retract_line
                    unretract_str = unretract_line
                return_to_str = f"G0 F{speed_travel}{return_location}; Return to print\n"
                return_final_str = model_replacement_pre_string_1 + retract_str + z_raise + model_replacement_pre_string_2 + load_str + purge_str_interface + return_to_str + "G91; Relative movement\n" + z_lower + unretract_str + return_e_reset_str + flow_rate_reset + "G90; Absolute movement\n" + ext_mode_str + ";" + str('-' * 26) + "; End of Material Change"

                ## Final changes to the 'Interface' change string
                startout_location_list = []
                startout_location_list = self.getReturnLocation(data, dnum, start_at_line, retract_speed)
                startout_location = startout_location_list[0]
                is_start_retraction = bool(startout_location_list[1])
                if not relative_ext_mode:
                    start_e_reset_str = "G92 E" + str(startout_location_list[2]) + "; Reset extruder\n"
                else:
                    start_e_reset_str = "G92 E0; Reset extruder\n"
                if is_start_retraction:
                    start_retract_str = ""
                    start_unretract_str = ""
                else:
                    start_retract_str = retract_line
                    start_unretract_str = unretract_line
                startout_to_str = "G0 F" + str(speed_travel) + startout_location + "; Return to print\n"
                startout_final_str = interface_replacement_pre_string_1 + start_retract_str + z_raise + interface_replacement_pre_string_2 + load_str + purge_str_model + startout_to_str + "G91; Relative movement\n" + z_lower + start_unretract_str + start_e_reset_str + flow_rate_str + "G90; Absolute movement\n" + ext_mode_str + ";" + str('-' * 26) + "; End of Material Change"

                ## Format the return_final_str
                temp_lines = return_final_str.split("\n")
                for temp_index, temp_line in enumerate(temp_lines):
                    if ";" in temp_line and not temp_line.startswith(";"):
                        temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (27 - len(temp_line.split(";")[0]))),1)
                return_final_str = "\n".join(temp_lines)
                ## Format the startout_final_str
                temp_lines = startout_final_str.split("\n")
                for temp_index, temp_line in enumerate(temp_lines):
                    if ";" in temp_line and not temp_line.startswith(";"):
                        temp_lines[temp_index] = temp_line.replace(temp_line.split(";")[0], temp_line.split(";")[0] + str(" " * (27 - len(temp_line.split(";")[0]))),1)
                startout_final_str = "\n".join(temp_lines)

                ## Add the new lines to the gcode
                lines[end_at_line] += "\n" + return_final_str
                lines[start_at_line] += "\n" + startout_final_str
                break
            data[dnum] = "\n".join(lines)
        return data

    # Get the return location and see if there was a retraction before the Interface
    def getReturnLocation(self, data: str, num: int, index: int, retract_speed: str):  #
        lines = data[num].split("\n")
        is_retraction = None
        ret_x = None
        ret_y = 0
        e_loc = None
        for back_num in range(index, -1, -1):
            if re.search("G1 F(\d*) E(\d.*)", lines[back_num]) is not None or re.search("G1 F(\d*) E-(\d.*)", lines[back_num]) is not None or "G10" in lines[back_num]:
                is_retraction = True
                if e_loc is None:
                    e_loc = self.getValue(lines[back_num], "E")
                    if "G10" in lines[back_num]:
                        e_loc = "0"
                if ret_x is not None: break
            if lines[back_num].startswith("G0") and " X" in lines[back_num] and " Y" in lines[back_num] and ret_x is None:
                ret_x = self.getValue(lines[back_num], "X")
                ret_y = self.getValue(lines[back_num], "Y")
                if is_retraction is not None: break
            if " X" in lines[back_num] and " Y" in lines[back_num] and " E" in lines[back_num]:
                if ret_x is None:
                    ret_x = self.getValue(lines[back_num], "X")
                    ret_y = self.getValue(lines[back_num], "Y")
                if e_loc is None:
                    e_loc = self.getValue(lines[back_num], "E")
                if is_retraction is None:
                    is_retraction = False
                    break

            ## If the interface is the first thing on the layer then go back to the previous layer.
            if ";LAYER:" in lines[back_num]:
                lines2 = data[num - 1].split("\n")
                for back_num2 in range(len(lines2)-1,0, -1):
                    if is_retraction is None and " E" in lines2[back_num2]:
                        ## Catch a retraction whether extrusions are Absolute or Relative or whether firmware retraction is enabled.
                        if re.search("G1 F(\d*) E-(\d.*)", lines2[back_num2]) is not None or re.search("G1 F(\d*) E(\d.*)", lines2[back_num2]) is not None or "G10" in lines2[back_num2]:
                            is_retraction = True
                            if e_loc is None:
                                e_loc = self.getValue(lines2[back_num2], "E")
                                if "G10" in lines2[back_num2]:
                                    e_loc = "0"
                        elif is_retraction is None and "G11" in lines2[back_num2]:
                            is_retraction = False
                        elif re.search("G1 F(\d*) X(\d.*) Y(\d.*) E(\d.*)", lines2[back_num2]) is not None or re.search("G1 X(\d.*) Y(\d.*) E(\d.*)", lines2[back_num2]) is not None:
                            is_retraction = False
                            if e_loc is None:
                                e_loc = self.getValue(lines2[back_num2], "E")
                                if "G11" in lines2[back_num2]:
                                    e_loc = "0"
                    if ret_x is None:
                        if " X" in lines2[back_num2] and " Y" in lines2[back_num2]:
                            ret_x = self.getValue(lines2[back_num2], "X")
                            ret_y = self.getValue(lines2[back_num2], "Y")
                    if e_loc is None and " E" in lines2[back_num2]:
                        e_loc = self.getValue(lines2[back_num2], "E")
                    if e_loc is not None and is_retraction is not None and ret_x is not None:
                        break
        ret_loc = " X" + str(ret_x) + " Y" + str(ret_y)
        return [ret_loc, is_retraction, e_loc]

    # Some printers will refuse a single long extrusion.  This breaks up long extrusions into 150mm chunks that should be acceptable to the firmware.
    ## the bool 'unload_filament' tells this whether to put together the unload string or the reload string.
    def getUnloadReloadScript(self, data: str, filament_dist: int, extrude_speed: int, retract_speed: int, unload_filament: bool, retract_dist: int)->str:
        if unload_filament:
            filament_str = "M83; Relative extrusion\nM400; Complete all moves\n"
            if filament_dist > 150:
                temp_unload = filament_dist
                while temp_unload > 150:
                    filament_str += "G1 F" + str(int(extrude_speed)) + " E-150; Unload some\n"
                    temp_unload -= 150
                if 0 < temp_unload <= 150:
                    filament_str += "G1 F" + str(int(extrude_speed)) + " E-" + str(temp_unload) + "; Unload the remainder\n"
            else:
                filament_str += "G1 F" + str(int(extrude_speed)) + " E-" + str(filament_dist) + "; Unload\n"
        ## The reload string must also be broken into chunks.  It has 2 parts...Fast reload and Slow reload.  (Purge is handled up above).
        elif not unload_filament:
            nozzle_size = CuraApplication.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_nozzle_size", "value")
            retraction_amount = CuraApplication.getInstance().getGlobalContainerStack().extruderList[0].getProperty("machine_nozzle_size", "value")
            firmware_retract = bool(CuraApplication.getInstance().getGlobalContainerStack().getProperty("machine_firmware_retract", "value"))
            filament_str = "M83; Relative extrusion\n"
            if int(filament_dist) > 0:
                if filament_dist * .9 > 150:
                    temp_dist = filament_dist - filament_dist * .1
                    while temp_dist > 150:
                        filament_str += "G1 F" + str(extrude_speed) + " E150" + "; Fast Reload\n"
                        temp_dist -= 150
                    if 0 < temp_dist <= 150:
                        filament_str += "G1 F" + str(extrude_speed) + " E" + str(round(temp_dist))  + "; Fast Reload\n"
                        filament_str += "G1 F" + str(round(float(nozzle_size) * 16.666 * 60)) + " E" + str(round(filament_dist * .1)) + "; Reload the last 10% slower to avoid ramming the nozzle\n"
                    else:
                        filament_str += "G1 F" + str(round(float(nozzle_size) * 16.666 * 60)) + " E" + str(round(filament_dist * .1)) + "; Reload the last 10% slower to avoid ramming the nozzle\n"
                else:
                    filament_str += "G1 F" + str(int(extrude_speed)) + " E" + str(round(filament_dist * .9)) + "; Fast Reload\n"
                    filament_str += "G1 F" + str(round(float(nozzle_size) * 16.666 * 60)) + " E" + str(round(filament_dist * .1))  + "; Reload the last 10% slower to avoid ramming the nozzle\n"
        return filament_str