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

# Uses -
# M220 S<factor in percent> - set speed factor override percentage
# M221 S<factor in percent> - set flow factor override percentage
# M221 S<factor in percent> T<0-#toolheads> - set flow factor override percentage for single extruder
# M104 S<temp> T<0-#toolheads> - set extruder <T> to target temperature <S>
# M140 S<temp> - set bed target temperature
# M106 S<PWM> - set fan speed to target speed <S>
# M605/606 to save and recall material settings on the UM2

from ..Script import Script
import re


# this was broken up into a separate class so the main ChangeZ script could be debugged outside of Cura
class ChangeAtZ(Script):

	version = "5.2.0"

	def getSettingDataString(self):
		return """{
			"name": "ChangeAtZ """ + self.version + """(Experimental)",
			"key": "ChangeAtZ",
			"metadata": {},
			"version": 2,
			"settings": {
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
					"label": "Behavior",
					"description": "Select behavior: Change value and keep it for the rest, Change value for single layer only",
					"type": "enum",
					"options": {
						"keep_value": "Keep value",
						"single_layer": "Single Layer"
					},
					"default_value": "keep_value"
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
				"caz_change_retractfeedrate": {
					"label": "Change Retract Feed Rate",
					"description": "Changes the retraction feed rate during print (M207)",
					"type": "bool",
					"default_value": false
				},
				"caz_retractfeedrate": {
					"label": "Retract Feed Rate",
					"description": "New Retract Feed Rate (units/s)",
					"unit": "units/s",
					"type": "float",
					"default_value": 40,
					"minimum_value": "0",
					"minimum_value_warning": "0",
					"maximum_value_warning": "100",
					"enabled": "caz_change_retractfeedrate"
				},
				"caz_change_retractlength": {
					"label": "Change Retract Length",
					"description": "Changes the retraction length during print (M207)",
					"type": "bool",
					"default_value": false
				},
				"caz_retractlength": {
					"label": "Retract Length",
					"description": "New Retract Length (units)",
					"unit": "units",
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

# The primary ChangeAtZ class that does all the gcode editing. This was broken out into an
# independent class so it could be debugged using a standard IDE
class ChangeAtZProcessor:

	TargetValues = {}
	IsApplyToSingleLayer = False
	LastE = None
	CurrentZ = None
	CurrentLayer = None
	IsTargetByLayer = True
	TargetLayer = None
	TargetZ = None
	LayerHeight = None
	RetractLength = 0

	# boots up the class with defaults
	def __init__(self):
		self.reset()

	# Modifies the given GCODE and injects the commands at the various targets
	def execute(self, data):

		# indicates if we should inject our defaults or not
		inject_defaults = True

		# our layer cursor
		index = 0

		for active_layer in data:

			# will hold our updated gcode
			modified_gcode = ""

			# mark all the defaults for deletion
			active_layer = self.markDefaultsForDeletion(active_layer)

			# break apart the layer into commands
			lines = active_layer.split("\n")

			# evaluate each command individually
			for line in lines:

				# skip empty lines
				if line.strip() == "":
					continue

				# update our layer number if applicable
				self.processLayerNumber(line)

				# update our layer height if applicable
				self.processLayerHeight(line)

				# skip this line if we're not there yet
				if not self.isTargetLayerOrHeight():

					# read any settings we might need
					self.processSetting(line)

					# if we haven't hit our target yet, leave the defaults as is (unmark them for deletion)
					if "[CAZD:DELETE:" in line:
						line = line.replace("[CAZD:DELETE:", "[CAZD:")

					# set our line
					modified_gcode += line + "\n"

					# skip to the next line
					continue

				# inject our defaults before linear motion commands
				if inject_defaults and ("G1" in line or "G0" in line):

					# inject the defaults
					modified_gcode += self.getTargetDefaults() + "\n"

					# mark that we've injected the defaults
					inject_defaults = False

				# append to our modified layer
				modified_gcode += self.processLinearMove(line) + "\n"

				# inject our defaults after the layer indicator
				if inject_defaults and ";LAYER:" in line:

					# inject the defaults
					modified_gcode += self.getTargetDefaults() + "\n"

					# mark that we've injected the defaults
					inject_defaults = False

			# remove any marked defaults
			modified_gcode = self.removeMarkedTargetDefaults(modified_gcode)

			# append our modified line
			data[index] = modified_gcode

			index += 1
		return data

	# Converts the command parameter to a float or returns the default
	@staticmethod
	def getFloatValue(line, key, default=None):

		# get the value from the command
		value = ChangeAtZProcessor.getValue(line, key, default)

		# stop here if it's the default
		if value == default:
			return value

		try:
			return float(value)
		except:
			return default

	# Converts the command parameter to a int or returns the default
	@staticmethod
	def getIntValue(line, key, default=None):

		# get the value from the command
		value = ChangeAtZProcessor.getValue(line, key, default)

		# stop here if it's the default
		if value == default:
			return value

		try:
			return int(value)
		except:
			return default

	# Handy function for reading a linear move command
	def getLinearMoveParams(self, line):

		# get our motion parameters
		feed_rate = self.getFloatValue(line, "F", None)
		x_coord = self.getFloatValue(line, "X", None)
		y_coord = self.getFloatValue(line, "Y", None)
		z_coord = self.getFloatValue(line, "Z", None)
		extrude_length = self.getFloatValue(line, "E", None)

		return extrude_length, feed_rate, x_coord, y_coord, z_coord

	# Returns the unmodified GCODE line from previous ChangeZ edits
	@staticmethod
	def getOriginalLine(line):

		# get the change at z original (cazo) details
		original_line = re.search(r"\[CAZO:(.*?):CAZO\]", line)

		# if we didn't get a hit, this is the original line
		if original_line is None:
			return line

		return original_line.group(1)

	# Builds the layer defaults based on the settings and returns the relevant GCODE lines
	def getTargetDefaults(self):

		# will hold all the default settings for the target layer
		defaults = []

		# used to trim other defaults
		defaults.append(";[CAZD:")

		# looking for wait for bed temp
		if "bedTemp" in self.TargetValues:
			defaults.append("M190 S" + str(self.TargetValues["bedTemp"]))

		# set our extruder temps
		if "extruderOne" in self.TargetValues:
			defaults.append("M109 S" + str(self.TargetValues["extruderOne"]))
		elif "extruderTwo" in self.TargetValues:
			defaults.append("M109 S" + str(self.TargetValues["extruderTwo"]))

		# set our fan speed
		if "fanSpeed" in self.TargetValues:

			# convert our fan speed percentage to PWM
			fan_speed = int((float(self.TargetValues["fanSpeed"]) / 100.0) * 255)

			# add our fan speed to the defaults
			defaults.append("M106 S" + str(fan_speed))

		# set global flow rate
		if "flowrate" in self.TargetValues:
			defaults.append("M221 S" + str(self.TargetValues["flowrate"]))

		# set extruder 0 flow rate
		if "flowrateOne" in self.TargetValues:
			defaults.append("M221 S" + str(self.TargetValues["flowrateOne"]) + " T0")

		# set second extruder flow rate
		if "flowrateTwo" in self.TargetValues:
			defaults.append("M221 S" + str(self.TargetValues["flowrateTwo"]) + " T1")

		# set feedrate percentage
		if "speed" in self.TargetValues:
			defaults.append("M220 S" + str(self.TargetValues["speed"]) + " T1")

		# set print rate percentage
		if "printspeed" in self.TargetValues:
			defaults.append(";PRINTSPEED " + str(self.TargetValues["printspeed"]) + "")

		# set retract rate
		if "retractfeedrate" in self.TargetValues:
			defaults.append(";RETRACTFEEDRATE " + str(self.TargetValues["retractfeedrate"]) + "")

		# set retract length
		if "retractlength" in self.TargetValues:
			defaults.append(";RETRACTLENGTH " + str(self.TargetValues["retractlength"]) + "")

		# used to trim other defaults
		defaults.append(";:CAZD]")

		# if there are no defaults, stop here
		if len(defaults) == 2:
			return ""

		# return our default block for this layer
		return "\n".join(defaults)

	# Allows retrieving values from the given GCODE line
	@staticmethod
	def getValue(line, key, default=None):

		if not key in line or (";" in line and line.find(key) > line.find(";") and not ";ChangeAtZ" in key and not ";LAYER:" in key):
			return default

		sub_part = line[line.find(key) + len(key):]  # allows for string lengths larger than 1
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
			return float(m.group(0))
		except:
			return default

	# Determines if the current line is at or below the target required to start modifying
	def isTargetLayerOrHeight(self):

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
	def markDefaultsForDeletion(layer):
		return re.sub(r";\[CAZD:", ";[CAZD:DELETE:", layer)

	# Grabs the current height
	def processLayerHeight(self, line):

		# stop here if we haven't entered a layer yet
		if self.CurrentLayer is None:
			return

		# expose the main command
		line_no_comments = self.stripComments(line)

		# stop here if this isn't a linear move command
		if not ("G1" in line_no_comments or "G0" in line_no_comments):
			return

		# stop here if we don't have a Z value defined, we can't get the height from this command
		if "Z" not in line_no_comments:
			return

		# get our value from the command
		current_z = self.getFloatValue(line_no_comments, "Z", None)

		# stop if there's no change
		if current_z == self.CurrentZ:
			return

		# set our current Z value
		self.CurrentZ = current_z

		# if we don't have a layer height yet, set it based on the current Z value
		if self.LayerHeight is None:
			self.LayerHeight = self.CurrentZ

	# Grabs the current layer number
	def processLayerNumber(self, line):

		# if this isn't a layer comment, stop here, nothing to update
		if ";LAYER:" not in line:
			return

		# get our current layer number
		current_layer = self.getIntValue(line, ";LAYER:", None)

		# this should never happen, but if our layer number hasn't changed, stop here
		if current_layer == self.CurrentLayer:
			return

		# update our current layer
		self.CurrentLayer = current_layer

	# Handles any linear moves in the current line
	def processLinearMove(self, line):

		# if it's not a linear motion command we're not interested
		if not ("G1" in line or "G0" in line):
			return line

		# always get our original line, otherwise the effect will be cumulative
		line = self.getOriginalLine(line)

		# get the details from our linear move command
		extrude_length, feed_rate, x_coord, y_coord, z_coord = self.getLinearMoveParams(line)

		# set our new line to our old line
		new_line = line

		# handle retract length
		new_line = self.processRetractLength(extrude_length, feed_rate, new_line, x_coord, y_coord, z_coord)

		# handle retract feed rate
		new_line = self.processRetractFeedRate(extrude_length, feed_rate, new_line, x_coord, y_coord, z_coord)

		# handle print speed adjustments
		new_line = self.processPrintSpeed(feed_rate, new_line)

		# set our current extrude position
		self.LastE = extrude_length if extrude_length is not None else self.LastE

		# if no changes have been made, stop here
		if new_line == line:
			return line

		# return our updated command
		return self.setOriginalLine(new_line, line)

	# Handles any changes to print speed for the given linear motion command
	def processPrintSpeed(self, feed_rate, new_line):

		# if we're not setting print speed or we don't have a feed rate, stop here
		if "printspeed" not in self.TargetValues or feed_rate is None:
			return new_line

		# get our requested print speed
		print_speed = int(self.TargetValues["printspeed"])

		# if they requested no change to print speed (ie: 100%), stop here
		if print_speed == 100:
			return new_line

		# get our feed rate from the command
		feed_rate = float(self.getValue(new_line, "F")) * (float(print_speed) / 100.0)

		# change our feed rate
		return self.replaceParameter(new_line, "F", feed_rate)

	# Handles any changes to retraction length for the given linear motion command
	def processRetractLength(self, extrude_length, feed_rate, new_line, x_coord, y_coord, z_coord):

		# if we don't have a retract length in the file we can't add one
		if self.RetractLength == 0:
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
		extrude_length -= (retract_length - self.RetractLength)

		# replace our extrude amount
		return self.replaceParameter(new_line, "E", extrude_length)

	# Used for picking out the retract length set by Cura
	def processRetractLengthSetting(self, line):

		# if it's not a linear move, we don't care
		if "G0" not in line and "G1" not in line:
			return

		# get the details from our linear move command
		extrude_length, feed_rate, x_coord, y_coord, z_coord = self.getLinearMoveParams(line)

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
		self.RetractLength = extrude_length

	# Handles any changes to retraction feed rate for the given linear motion command
	def processRetractFeedRate(self, extrude_length, feed_rate, new_line, x_coord, y_coord, z_coord):

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
		return self.replaceParameter(new_line, "F", retract_feed_rate)

	# Used for finding settings in the print file before we process anything else
	def processSetting(self, line):

		# if we're in layers already we're out of settings
		if self.CurrentLayer is not None:
			return

		# check our retract length
		self.processRetractLengthSetting(line)

	# Removes all the ChangeZ layer defaults from the given layer
	@staticmethod
	def removeMarkedTargetDefaults(layer):
		return re.sub(r";\[CAZD:DELETE:[\s\S]+?:CAZD\](\n|$)", "", layer)

	# Easy function for replacing any GCODE parameter variable in a given GCODE command
	@staticmethod
	def replaceParameter(line, key, value):
		return re.sub(r"(^|\s)" + key + r"[\d\.]+(\s|$)", r"\1" + key + str(value) + r"\2", line)

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
		self.RetractLength = 0

	# Sets the original GCODE line in a given GCODE command
	@staticmethod
	def setOriginalLine(line, original):
		return line + ";[CAZO:" + original + ":CAZO]"

	# Removes the gcode comments from a given gcode command
	@staticmethod
	def stripComments(line):
		return re.sub(r";.*?$", "", line).strip()


def debug():
	# get our input file
	file = r"PATH_TO_SOME_GCODE.gcode"

	# read the whole thing
	f = open(file, "r")
	gcode = f.read()
	f.close()

	# boot up change
	caz_instance = ChangeAtZProcessor()
	caz_instance.IsTargetByLayer = False
	caz_instance.TargetZ = 5
	caz_instance.TargetValues["printspeed"] = 100
	caz_instance.TargetValues["retractfeedrate"] = 60

	# process gcode
	gcode = debug_iteration(gcode, caz_instance)

	# write our file
	debug_write(gcode, file + ".1.modified")

	caz_instance.reset()
	caz_instance.IsTargetByLayer = False
	caz_instance.TargetZ = 10.5
	caz_instance.TargetValues["bedTemp"] = 75.111
	caz_instance.TargetValues["printspeed"] = 150
	caz_instance.TargetValues["retractfeedrate"] = 40.555
	caz_instance.TargetValues["retractlength"] = 10.3333

	# and again
	gcode = debug_iteration(gcode, caz_instance)

	# write our file
	debug_write(gcode, file + ".2.modified")

	caz_instance.reset()
	caz_instance.IsTargetByLayer = False
	caz_instance.TargetZ = 15
	caz_instance.TargetValues["bedTemp"] = 80
	caz_instance.TargetValues["printspeed"] = 100
	caz_instance.TargetValues["retractfeedrate"] = 10
	caz_instance.TargetValues["retractlength"] = 0

	# and again
	gcode = debug_iteration(gcode, caz_instance)

	# write our file
	debug_write(gcode, file + ".3.modified")


def debug_write(gcode, file):
	# write our file
	f = open(file, "w")
	f.write(gcode)
	f.close()


def debug_iteration(gcode, caz_instance):
	index = 0

	# break apart the GCODE like cura
	layers = re.split(r"^;LAYER:\d+\n", gcode)

	# add the layer numbers back
	for layer in layers:

		# if this is the first layer, skip it, basically
		if index == 0:
			# leave our first layer as is
			layers[index] = layer

			# move the cursor
			index += 1

			# skip to the next layer
			continue

		layers[index] = ";LAYER:" + str(index - 1) + ";\n" + layer

	return "".join(caz_instance.execute(layers))

# debug()
