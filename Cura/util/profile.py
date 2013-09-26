from __future__ import absolute_import
from __future__ import division
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os, traceback, math, re, zlib, base64, time, sys, platform, glob, string, stat, types
import cPickle as pickle
if sys.version_info[0] < 3:
	import ConfigParser
else:
	import configparser as ConfigParser

from Cura.util import resources
from Cura.util import version
from Cura.util import validators

#The settings dictionary contains a key/value reference to all possible settings. With the setting name as key.
settingsDictionary = {}
#The settings list is used to keep a full list of all the settings. This is needed to keep the settings in the proper order,
# as the dictionary will not contain insertion order.
settingsList = []

#Currently selected machine (by index) Cura support multiple machines in the same preferences and can switch between them.
# Each machine has it's own index and unique name.
_selectedMachineIndex = 0

class setting(object):
	#A setting object contains a configuration setting. These are globally accessible trough the quick access functions
	# and trough the settingsDictionary function.
	# Settings can be:
	# * profile settings (settings that effect the slicing process and the print result)
	# * preferences (settings that effect how cura works and acts)
	# * machine settings (settings that relate to the physical configuration of your machine)
	# * alterations (bad name copied from Skeinforge. These are the start/end code pieces)
	# Settings have validators that check if the value is valid, but do not prevent invalid values!
	# Settings have conditions that enable/disable this setting depending on other settings. (Ex: Dual-extrusion)
	def __init__(self, name, default, type, category, subcategory):
		self._name = name
		self._label = name
		self._tooltip = ''
		self._default = unicode(default)
		self._values = []
		self._type = type
		self._category = category
		self._subcategory = subcategory
		self._validators = []
		self._conditions = []

		if type is types.FloatType:
			validators.validFloat(self)
		elif type is types.IntType:
			validators.validInt(self)

		global settingsDictionary
		settingsDictionary[name] = self
		global settingsList
		settingsList.append(self)

	def setLabel(self, label, tooltip = ''):
		self._label = label
		self._tooltip = tooltip
		return self

	def setRange(self, minValue=None, maxValue=None):
		if len(self._validators) < 1:
			return
		self._validators[0].minValue = minValue
		self._validators[0].maxValue = maxValue
		return self

	def getLabel(self):
		return _(self._label)

	def getTooltip(self):
		return _(self._tooltip)

	def getCategory(self):
		return self._category

	def getSubCategory(self):
		return self._subcategory

	def isPreference(self):
		return self._category == 'preference'

	def isMachineSetting(self):
		return self._category == 'machine'

	def isAlteration(self):
		return self._category == 'alteration'

	def isProfile(self):
		return not self.isAlteration() and not self.isPreference() and not self.isMachineSetting()

	def getName(self):
		return self._name

	def getType(self):
		return self._type

	def getValue(self, index = None):
		if index is None:
			index = self.getValueIndex()
		if index >= len(self._values):
			return self._default
		return self._values[index]

	def getDefault(self):
		return self._default

	def setValue(self, value, index = None):
		if index is None:
			index = self.getValueIndex()
		while index >= len(self._values):
			self._values.append(self._default)
		self._values[index] = unicode(value)

	def getValueIndex(self):
		if self.isMachineSetting():
			global _selectedMachineIndex
			return _selectedMachineIndex
		return 0

	def validate(self):
		result = validators.SUCCESS
		msgs = []
		for validator in self._validators:
			res, err = validator.validate()
			if res == validators.ERROR:
				result = res
			elif res == validators.WARNING and result != validators.ERROR:
				result = res
			if res != validators.SUCCESS:
				msgs.append(err)
		return result, '\n'.join(msgs)

	def addCondition(self, conditionFunction):
		self._conditions.append(conditionFunction)

	def checkConditions(self):
		for condition in self._conditions:
			if not condition():
				return False
		return True

#########################################################
## Settings
#########################################################

#Define a fake _() function to fake the gettext tools in to generating strings for the profile settings.
def _(n):
	return n

setting('layer_height',              0.1, float, 'basic',    _('Quality')).setRange(0.0001).setLabel(_("Layer height (mm)"), _("Layer height in millimeters.\nThis is the most important setting to determine the quality of your print. Normal quality prints are 0.1mm, high quality is 0.06mm. You can go up to 0.25mm with an Ultimaker for very fast prints at low quality."))
setting('wall_thickness',            0.8, float, 'basic',    _('Quality')).setRange(0.0).setLabel(_("Shell thickness (mm)"), _("Thickness of the outside shell in the horizontal direction.\nThis is used in combination with the nozzle size to define the number\nof perimeter lines and the thickness of those perimeter lines."))
setting('retraction_enable',       False, bool,  'basic',    _('Quality')).setLabel(_("Enable retraction"), _("Retract the filament when the nozzle is moving over a none-printed area. Details about the retraction can be configured in the advanced tab."))
setting('solid_layer_thickness',     0.6, float, 'basic',    _('Fill')).setRange(0).setLabel(_("Bottom/Top thickness (mm)"), _("This controls the thickness of the bottom and top layers, the amount of solid layers put down is calculated by the layer thickness and this value.\nHaving this value a multiple of the layer thickness makes sense. And keep it near your wall thickness to make an evenly strong part."))
setting('fill_density',               20, float, 'basic',    _('Fill')).setRange(0, 100).setLabel(_("Fill Density (%)"), _("This controls how densely filled the insides of your print will be. For a solid part use 100%, for an empty part use 0%. A value around 20% is usually enough.\nThis won't effect the outside of the print and only adjusts how strong the part becomes."))
setting('nozzle_size',               0.4, float, 'advanced', _('Machine')).setRange(0.1,10).setLabel(_("Nozzle size (mm)"), _("The nozzle size is very important, this is used to calculate the line width of the infill, and used to calculate the amount of outside wall lines and thickness for the wall thickness you entered in the print settings."))
setting('print_speed',                50, float, 'basic',    _('Speed & Temperature')).setRange(1).setLabel(_("Print speed (mm/s)"), _("Speed at which printing happens. A well adjusted Ultimaker can reach 150mm/s, but for good quality prints you want to print slower. Printing speed depends on a lot of factors. So you will be experimenting with optimal settings for this."))
setting('print_temperature',         220, int,   'basic',    _('Speed & Temperature')).setRange(0,340).setLabel(_("Printing temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_temperature2',          0, int,   'basic',    _('Speed & Temperature')).setRange(0,340).setLabel(_("2nd nozzle temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_temperature3',          0, int,   'basic',    _('Speed & Temperature')).setRange(0,340).setLabel(_("3th nozzle temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_temperature4',          0, int,   'basic',    _('Speed & Temperature')).setRange(0,340).setLabel(_("4th nozzle temperature (C)"), _("Temperature used for printing. Set at 0 to pre-heat yourself.\nFor PLA a value of 210C is usually used.\nFor ABS a value of 230C or higher is required."))
setting('print_bed_temperature',      70, int,   'basic',    _('Speed & Temperature')).setRange(0,340).setLabel(_("Bed temperature (C)"), _("Temperature used for the heated printer bed. Set at 0 to pre-heat yourself."))
setting('support',                'None', ['None', 'Touching buildplate', 'Everywhere'], 'basic', _('Support')).setLabel(_("Support type"), _("Type of support structure build.\n\"Touching buildplate\" is the most commonly used support setting.\n\nNone does not do any support.\nTouching buildplate only creates support where the support structure will touch the build platform.\nEverywhere creates support even on top of parts of the model."))
setting('platform_adhesion',      'None', ['None', 'Brim', 'Raft'], 'basic', _('Support')).setLabel(_("Platform adhesion type"), _("Different options that help in preventing corners from lifting due to warping.\nBrim adds a single layer thick flat area around your object which is easy to cut off afterwards, and the recommended option.\nRaft adds a thick raster at below the object and a thin interface between this and your object.\n(Note that enabling the brim or raft disables the skirt)"))
setting('support_dual_extrusion',  'Both', ['Both', 'First extruder', 'Second extruder'], 'basic', _('Support')).setLabel(_("Support dual extrusion"), _("Which extruder to use for support material, for break-away support you can use both extruders.\nBut if one of the materials is more expensive then the other you could select an extruder to use for support material. This causes more extruder switches.\nYou can also use the 2nd extruder for soluble support materials."))
setting('filament_diameter',        2.85, float, 'basic',    _('Filament')).setRange(1).setLabel(_("Diameter (mm)"), _("Diameter of your filament, as accurately as possible.\nIf you cannot measure this value you will have to calibrate it, a higher number means less extrusion, a smaller number generates more extrusion."))
setting('filament_diameter2',          0, float, 'basic',    _('Filament')).setRange(0).setLabel(_("Diameter2 (mm)"), _("Diameter of your filament for the 2nd nozzle. Use 0 to use the same diameter as for nozzle 1."))
setting('filament_diameter3',          0, float, 'basic',    _('Filament')).setRange(0).setLabel(_("Diameter3 (mm)"), _("Diameter of your filament for the 3th nozzle. Use 0 to use the same diameter as for nozzle 1."))
setting('filament_diameter4',          0, float, 'basic',    _('Filament')).setRange(0).setLabel(_("Diameter4 (mm)"), _("Diameter of your filament for the 4th nozzle. Use 0 to use the same diameter as for nozzle 1."))
setting('filament_flow',            100., float, 'basic',    _('Filament')).setRange(1,300).setLabel(_("Flow (%)"), _("Flow compensation, the amount of material extruded is multiplied by this value"))
setting('retraction_speed',         40.0, float, 'advanced', _('Retraction')).setRange(0.1).setLabel(_("Speed (mm/s)"), _("Speed at which the filament is retracted, a higher retraction speed works better. But a very high retraction speed can lead to filament grinding."))
setting('retraction_amount',         4.5, float, 'advanced', _('Retraction')).setRange(0).setLabel(_("Distance (mm)"), _("Amount of retraction, set at 0 for no retraction at all. A value of 4.5mm seems to generate good results."))
setting('retraction_dual_amount',   16.5, float, 'advanced', _('Retraction')).setRange(0).setLabel(_("Dual extrusion switch amount (mm)"), _("Amount of retraction when switching nozzle with dual-extrusion, set at 0 for no retraction at all. A value of 16.0mm seems to generate good results."))
setting('retraction_min_travel',     1.5, float, 'expert',   _('Retraction')).setRange(0).setLabel(_("Minimum travel (mm)"), _("Minimum amount of travel needed for a retraction to happen at all. To make sure you do not get a lot of retractions in a small area."))
setting('retraction_combing',       True, bool,  'expert',   _('Retraction')).setLabel(_("Enable combing"), _("Combing is the act of avoiding holes in the print for the head to travel over. If combing is disabled the printer head moves straight from the start point to the end point and it will always retract."))
setting('retraction_minimal_extrusion',0.5, float,'expert',  _('Retraction')).setRange(0).setLabel(_("Minimal extrusion before retracting (mm)"), _("The minimal amount of extrusion that needs to be done before retracting again if a retraction needs to happen before this minimal is reached the retraction is ignored.\nThis avoids retraction a lot on the same piece of filament which flattens the filament and causes grinding issues."))
setting('bottom_thickness',          0.3, float, 'advanced', _('Quality')).setRange(0).setLabel(_("Initial layer thickness (mm)"), _("Layer thickness of the bottom layer. A thicker bottom layer makes sticking to the bed easier. Set to 0.0 to have the bottom layer thickness the same as the other layers."))
setting('object_sink',               0.0, float, 'advanced', _('Quality')).setLabel(_("Cut off object bottom (mm)"), _("Sinks the object into the platform, this can be used for objects that do not have a flat bottom and thus create a too small first layer."))
#setting('enable_skin',             False, bool,  'advanced', _('Quality')).setLabel(_("Duplicate outlines"), _("Skin prints the outer lines of the prints twice, each time with half the thickness. This gives the illusion of a higher print quality."))
setting('overlap_dual',              0.2, float, 'advanced', _('Quality')).setLabel(_("Dual extrusion overlap (mm)"), _("Add a certain amount of overlapping extrusion on dual-extrusion prints. This bonds the different colors better together."))
setting('travel_speed',            150.0, float, 'advanced', _('Speed')).setRange(0.1).setLabel(_("Travel speed (mm/s)"), _("Speed at which travel moves are done, a high quality build Ultimaker can reach speeds of 250mm/s. But some machines might miss steps then."))
setting('bottom_layer_speed',         20, float, 'advanced', _('Speed')).setRange(0.1).setLabel(_("Bottom layer speed (mm/s)"), _("Print speed for the bottom layer, you want to print the first layer slower so it sticks better to the printer bed."))
setting('infill_speed',              0.0, float, 'advanced', _('Speed')).setRange(0.0).setLabel(_("Infill speed (mm/s)"), _("Speed at which infill parts are printed. If set to 0 then the print speed is used for the infill. Printing the infill faster can greatly reduce printing, but this can negatively effect print quality.."))
setting('cool_min_layer_time',         5, float, 'advanced', _('Cool')).setRange(0).setLabel(_("Minimal layer time (sec)"), _("Minimum time spend in a layer, gives the layer time to cool down before the next layer is put on top. If the layer will be placed down too fast the printer will slow down to make sure it has spend at least this amount of seconds printing this layer."))
setting('fan_enabled',              True, bool,  'advanced', _('Cool')).setLabel(_("Enable cooling fan"), _("Enable the cooling fan during the print. The extra cooling from the cooling fan is essential during faster prints."))

setting('skirt_line_count',            1, int,   'expert', 'Skirt').setRange(0).setLabel(_("Line count"), _("The skirt is a line drawn around the object at the first layer. This helps to prime your extruder, and to see if the object fits on your platform.\nSetting this to 0 will disable the skirt. Multiple skirt lines can help priming your extruder better for small objects."))
setting('skirt_gap',                 3.0, float, 'expert', 'Skirt').setRange(0).setLabel(_("Start distance (mm)"), _("The distance between the skirt and the first layer.\nThis is the minimal distance, multiple skirt lines will be put outwards from this distance."))
setting('skirt_minimal_length',    150.0, float, 'expert', 'Skirt').setRange(0).setLabel(_("Minimal length (mm)"), _("The minimal length of the skirt, if this minimal length is not reached it will add more skirt lines to reach this minimal lenght.\nNote: If the line count is set to 0 this is ignored."))
#setting('max_z_speed',               3.0, float, 'expert',   _('Speed')).setRange(0.1).setLabel(_("Max Z speed (mm/s)"), _("Speed at which Z moves are done. When you Z axis is properly lubricated you can increase this for less Z blob."))
#setting('retract_on_jumps_only',    True, bool,  'expert',   _('Retraction')).setLabel(_('Retract on jumps only'), _('Only retract when we are making a move that is over a hole in the model, else retract on every move. This effects print quality in different ways.'))
setting('fan_layer',                   1, int,   'expert',   _('Cool')).setRange(0).setLabel(_("Fan on layer number"), _("The layer at which the fan is turned on. The first layer is layer 0. The first layer can stick better if you turn on the fan on, on the 2nd layer."))
setting('fan_speed',                 100, int,   'expert',   _('Cool')).setRange(0,100).setLabel(_("Fan speed min (%)"), _("When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Minimal fan speed is used if the layer is not slowed down due to cooling."))
setting('fan_speed_max',             100, int,   'expert',   _('Cool')).setRange(0,100).setLabel(_("Fan speed max (%)"), _("When the fan is turned on, it is enabled at this speed setting. If cool slows down the layer, the fan is adjusted between the min and max speed. Maximal fan speed is used if the layer is slowed down due to cooling by more than 200%."))
setting('cool_min_feedrate',          10, float, 'expert',   _('Cool')).setRange(0).setLabel(_("Minimum speed (mm/s)"), _("The minimal layer time can cause the print to slow down so much it starts to ooze. The minimal feedrate protects against this. Even if a print gets slown down it will never be slower than this minimal speed."))
setting('cool_head_lift',          False, bool,  'expert',   _('Cool')).setLabel(_("Cool head lift"), _("Lift the head if the minimal speed is hit because of cool slowdown, and wait the extra time so the minimal layer time is always hit."))
#setting('extra_base_wall_thickness', 0.0, float, 'expert',   'Accuracy').setRange(0).setLabel(_("Extra Wall thickness for bottom/top (mm)"), _("Additional wall thickness of the bottom and top layers."))
#setting('sequence', 'Loops > Perimeter > Infill', ['Loops > Perimeter > Infill', 'Loops > Infill > Perimeter', 'Infill > Loops > Perimeter', 'Infill > Perimeter > Loops', 'Perimeter > Infill > Loops', 'Perimeter > Loops > Infill'], 'expert', 'Sequence')
#setting('force_first_layer_sequence', True, bool, 'expert', 'Sequence').setLabel(_('Force first layer sequence'), _('This setting forces the order of the first layer to be \'Perimeter > Loops > Infill\''))
#setting('infill_type', 'Line', ['Line', 'Grid Circular', 'Grid Hexagonal', 'Grid Rectangular'], 'expert', _('Infill')).setLabel(_("Infill pattern"), _("Pattern of the none-solid infill. Line is default, but grids can provide a strong print."))
setting('solid_top', True, bool, 'expert', _('Infill')).setLabel(_("Solid infill top"), _("Create a solid top surface, if set to false the top is filled with the fill percentage. Useful for cups/vases."))
setting('solid_bottom', True, bool, 'expert', _('Infill')).setLabel(_("Solid infill bottom"), _("Create a solid bottom surface, if set to false the bottom is filled with the fill percentage. Useful for buildings."))
setting('fill_overlap', 15, int, 'expert', _('Infill')).setRange(0,100).setLabel(_("Infill overlap (%)"), _("Amount of overlap between the infill and the walls. There is a slight overlap with the walls and the infill so the walls connect firmly to the infill."))
setting('support_fill_rate', 20, int, 'expert', _('Support')).setRange(0,100).setLabel(_("Fill amount (%)"), _("Amount of infill structure in the support material, less material gives weaker support which is easier to remove. 20% seems to be a good average."))
setting('support_xy_distance', 0.7, float, 'expert', _('Support')).setRange(0,10).setLabel(_("Distance X/Y (mm)"), _("Distance of the support material from the print, in the X/Y directions.\n0.7mm gives a nice distance from the print so the support does not stick to the print."))
setting('support_z_distance', 0.15, float, 'expert', _('Support')).setRange(0,10).setLabel(_("Distance Z (mm)"), _("Distance from the top/bottom of the support to the print. A small gap here makes it easier to remove the support but makes the print a bit uglier.\n0.15mm gives a good seperation of the support material."))
#setting('support_distance',  0.5, float, 'expert', _('Support')).setRange(0).setLabel(_("Distance from object (mm)"), _("Distance between the support structure and the object. Empty gap in which no support structure is printed."))
#setting('joris', False, bool, 'expert', 'Joris').setLabel(_("Spiralize the outer contour"), _("[Joris] is a code name for smoothing out the Z move of the outer edge. This will create a steady Z increase over the whole print. It is intended to be used with a single walled wall thickness to make cups/vases."))
#setting('bridge_speed', 100, int, 'expert', 'Bridge').setRange(0,100).setLabel(_("Bridge speed (%)"), _("Speed at which layers with bridges are printed, compared to normal printing speed."))
setting('brim_line_count', 20, int, 'expert', _('Brim')).setRange(1,100).setLabel(_("Brim line amount"), _("The amount of lines used for a brim, more lines means a larger brim which sticks better, but this also makes your effective print area smaller."))
setting('raft_margin', 5, float, 'expert', _('Raft')).setRange(0).setLabel(_("Extra margin (mm)"), _("If the raft is enabled, this is the extra raft area around the object which is also rafted. Increasing this margin will create a stronger raft while using more material and leaving less are for your print."))
setting('raft_line_spacing', 1.0, float, 'expert', _('Raft')).setRange(0).setLabel(_("Line spacing (mm)"), _("When you are using the raft this is the distance between the centerlines of the raft line."))
setting('raft_base_thickness', 0.3, float, 'expert', _('Raft')).setRange(0).setLabel(_("Base thickness (mm)"), _("When you are using the raft this is the thickness of the base layer which is put down."))
setting('raft_base_linewidth', 0.7, float, 'expert', _('Raft')).setRange(0).setLabel(_("Base line width (mm)"), _("When you are using the raft this is the width of the base layer lines which are put down."))
setting('raft_interface_thickness', 0.2, float, 'expert', _('Raft')).setRange(0).setLabel(_("Interface thickness (mm)"), _("When you are using the raft this is the thickness of the interface layer which is put down."))
setting('raft_interface_linewidth', 0.2, float, 'expert', _('Raft')).setRange(0).setLabel(_("Interface line width (mm)"), _("When you are using the raft this is the width of the interface layer lines which are put down."))
#setting('hop_on_move', False, bool, 'expert', 'Hop').setLabel(_("Enable hop on move"), _("When moving from print position to print position, raise the printer head 0.2mm so it does not knock off the print (experimental)."))
setting('fix_horrible_union_all_type_a', False, bool, 'expert', _('Fix horrible')).setLabel(_("Combine everything (Type-A)"), _("This expert option adds all parts of the model together. The result is usually that internal cavities disappear. Depending on the model this can be intended or not. Enabling this option is at your own risk. Type-A is depended on the model normals and tries to keep some internal holes intact. Type-B ignores all internal holes and only keeps the outside shape per layer."))
setting('fix_horrible_union_all_type_b', False, bool, 'expert', _('Fix horrible')).setLabel(_("Combine everything (Type-B)"), _("This expert option adds all parts of the model together. The result is usually that internal cavities disappear. Depending on the model this can be intended or not. Enabling this option is at your own risk. Type-A is depended on the model normals and tries to keep some internal holes intact. Type-B ignores all internal holes and only keeps the outside shape per layer."))
setting('fix_horrible_use_open_bits', False, bool, 'expert', _('Fix horrible')).setLabel(_("Keep open faces"), _("This expert option keeps all the open bits of the model intact. Normally Cura tries to stitch up small holes and remove everything with big holes, but this option keeps bits that are not properly part of anything and just goes with whatever it is left. This option is usually not what you want, but it might enable you to slice models otherwise failing to produce proper paths.\nAs with all \"Fix horrible\" options, results may vary and use at your own risk."))
setting('fix_horrible_extensive_stitching', False, bool, 'expert', _('Fix horrible')).setLabel(_("Extensive stitching"), _("Extrensive stitching tries to fix up open holes in the model by closing the hole with touching polygons. This algorthm is quite expensive and could introduce a lot of processing time.\nAs with all \"Fix horrible\" options, results may vary and use at your own risk."))

setting('plugin_config', '', str, 'hidden', 'hidden')
setting('object_center_x', -1, float, 'hidden', 'hidden')
setting('object_center_y', -1, float, 'hidden', 'hidden')

setting('start.gcode', """;Sliced at: {day} {date} {time}
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Print time: {print_time}
;Filament used: {filament_amount}m {filament_weight}g
;Filament cost: {filament_cost}
G21        ;metric values
G90        ;absolute positioning
M107       ;start with the fan off

G28 X0 Y0  ;move X/Y to min endstops
G28 Z0     ;move Z to min endstops

G1 Z15.0 F{travel_speed} ;move the platform down 15mm

G92 E0                  ;zero the extruded length
G1 F200 E3              ;extrude 3mm of feed stock
G92 E0                  ;zero the extruded length again
G1 F{travel_speed}
M117 Printing...
""", str, 'alteration', 'alteration')
#######################################################################################
setting('end.gcode', """;End GCode
M104 S0                     ;extruder heater off
M140 S0                     ;heated bed heater off (if you have it)

G91                                    ;relative positioning
G1 E-1 F300                            ;retract the filament a bit before lifting the nozzle, to release some of the pressure
G1 Z+0.5 E-5 X-20 Y-20 F{travel_speed} ;move Z up a bit and retract filament even more
G28 X0 Y0                              ;move X/Y to min endstops, so the head is out of the way

M84                         ;steppers off
G90                         ;absolute positioning
""", str, 'alteration', 'alteration')
#######################################################################################
setting('start2.gcode', """;Sliced at: {day} {date} {time}
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Print time: {print_time}
;Filament used: {filament_amount}m {filament_weight}g
;Filament cost: {filament_cost}
G21        ;metric values
G90        ;absolute positioning
M107       ;start with the fan off

G28 X0 Y0  ;move X/Y to min endstops
G28 Z0     ;move Z to min endstops

G1 Z15.0 F{travel_speed} ;move the platform down 15mm

T1
G92 E0                  ;zero the extruded length
G1 F200 E10             ;extrude 10mm of feed stock
G92 E0                  ;zero the extruded length again
G1 F200 E-{retraction_dual_amount}

T0
G92 E0                  ;zero the extruded length
G1 F200 E10              ;extrude 10mm of feed stock
G92 E0                  ;zero the extruded length again
G1 F{travel_speed}
M117 Printing...
""", str, 'alteration', 'alteration')
#######################################################################################
setting('end2.gcode', """;End GCode
M104 T0 S0                     ;extruder heater off
M104 T1 S0                     ;extruder heater off
M140 S0                     ;heated bed heater off (if you have it)

G91                                    ;relative positioning
G1 E-1 F300                            ;retract the filament a bit before lifting the nozzle, to release some of the pressure
G1 Z+0.5 E-5 X-20 Y-20 F{travel_speed} ;move Z up a bit and retract filament even more
G28 X0 Y0                              ;move X/Y to min endstops, so the head is out of the way

M84                         ;steppers off
G90                         ;absolute positioning
""", str, 'alteration', 'alteration')
#######################################################################################
setting('support_start.gcode', '', str, 'alteration', 'alteration')
setting('support_end.gcode', '', str, 'alteration', 'alteration')
setting('cool_start.gcode', '', str, 'alteration', 'alteration')
setting('cool_end.gcode', '', str, 'alteration', 'alteration')
setting('replace.csv', '', str, 'alteration', 'alteration')
#######################################################################################
setting('nextobject.gcode', """;Move to next object on the platform. clear_z is the minimal z height we need to make sure we do not hit any objects.
G92 E0

G91                                    ;relative positioning
G1 E-1 F300                            ;retract the filament a bit before lifting the nozzle, to release some of the pressure
G1 Z+0.5 E-5 F{travel_speed}           ;move Z up a bit and retract filament even more
G90                                    ;absolute positioning

G1 Z{clear_z} F{max_z_speed}
G92 E0
G1 X{object_center_x} Y{object_center_y} F{travel_speed}
G1 F200 E6
G92 E0
""", str, 'alteration', 'alteration')
#######################################################################################
setting('switchExtruder.gcode', """;Switch between the current extruder and the next extruder, when printing with multiple extruders.
G92 E0
G1 E-36 F5000
G92 E0
T{extruder}
G1 X{new_x} Y{new_y} Z{new_z} F{travel_speed}
G1 E36 F5000
G92 E0
""", str, 'alteration', 'alteration')

setting('startMode', 'Simple', ['Simple', 'Normal'], 'preference', 'hidden')
setting('lastFile', os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'example', 'UltimakerRobot_support.stl')), str, 'preference', 'hidden')
setting('save_profile', 'False', bool, 'preference', 'hidden').setLabel(_("Save profile on slice"), _("When slicing save the profile as [stl_file]_profile.ini next to the model."))
setting('filament_cost_kg', '0', float, 'preference', 'hidden').setLabel(_("Cost (price/kg)"), _("Cost of your filament per kg, to estimate the cost of the final print."))
setting('filament_cost_meter', '0', float, 'preference', 'hidden').setLabel(_("Cost (price/m)"), _("Cost of your filament per meter, to estimate the cost of the final print."))
setting('auto_detect_sd', 'True', bool, 'preference', 'hidden').setLabel(_("Auto detect SD card drive"), _("Auto detect the SD card. You can disable this because on some systems external hard-drives or USB sticks are detected as SD card."))
setting('check_for_updates', 'True', bool, 'preference', 'hidden').setLabel(_("Check for updates"), _("Check for newer versions of Cura on startup"))
setting('submit_slice_information', 'False', bool, 'preference', 'hidden').setLabel(_("Send usage statistics"), _("Submit anonymous usage information to improve next versions of Cura"))
setting('youmagine_token', '', str, 'preference', 'hidden')
setting('filament_physical_density', '1240', float, 'preference', 'hidden').setRange(500.0, 3000.0).setLabel(_("Density (kg/m3)"), _("Weight of the filament per m3. Around 1240 for PLA. And around 1040 for ABS. This value is used to estimate the weight if the filament used for the print."))
setting('active_machine', '0', int, 'preference', 'hidden')

setting('model_colour', '#FFC924', str, 'preference', 'hidden').setLabel(_('Model colour')
setting('model_colour2', '#CB3030', str, 'preference', 'hidden').setLabel(_('Model colour (2)'))
setting('model_colour3', '#DDD93C', str, 'preference', 'hidden').setLabel(_('Model colour (3)'))
setting('model_colour4', '#4550D3', str, 'preference', 'hidden').setLabel(_('Model colour (4)'))

setting('window_maximized', 'True', bool, 'preference', 'hidden')
setting('window_pos_x', '-1', float, 'preference', 'hidden')
setting('window_pos_y', '-1', float, 'preference', 'hidden')
setting('window_width', '-1', float, 'preference', 'hidden')
setting('window_height', '-1', float, 'preference', 'hidden')
setting('window_normal_sash', '320', float, 'preference', 'hidden')

setting('machine_name', '', str, 'machine', 'hidden')
setting('machine_type', 'unknown', str, 'machine', 'hidden') #Ultimaker, Ultimaker2, RepRap
setting('machine_width', '205', float, 'machine', 'hidden').setLabel(_("Maximum width (mm)"), _("Size of the machine in mm"))
setting('machine_depth', '205', float, 'machine', 'hidden').setLabel(_("Maximum depth (mm)"), _("Size of the machine in mm"))
setting('machine_height', '200', float, 'machine', 'hidden').setLabel(_("Maximum height (mm)"), _("Size of the machine in mm"))
setting('machine_center_is_zero', 'False', bool, 'machine', 'hidden')
setting('ultimaker_extruder_upgrade', 'False', bool, 'machine', 'hidden')
setting('has_heated_bed', 'False', bool, 'machine', 'hidden').setLabel(_("Heated bed"), _("If you have an heated bed, this enabled heated bed settings (requires restart)"))
setting('gcode_flavor', 'RepRap (Marlin/Sprinter)', ['RepRap (Marlin/Sprinter)', 'UltiGCode'], 'machine', 'hidden').setLabel(_("GCode Flavor"), _("Flavor of generated GCode.\nRepRap is normal 5D GCode which works on Marlin/Sprinter based firmwares.\nUltiGCode is a variation of the RepRap GCode which puts more settings in the machine instead of the slicer."))
setting('extruder_amount', '1', ['1','2','3','4'], 'machine', 'hidden').setLabel(_("Extruder count"), _("Amount of extruders in your machine."))
setting('extruder_offset_x1', '-21.6', float, 'machine', 'hidden').setLabel(_("Offset X"), _("The offset of your secondary extruder compared to the primary."))
setting('extruder_offset_y1', '0.0', float, 'machine', 'hidden').setLabel(_("Offset Y"), _("The offset of your secondary extruder compared to the primary."))
setting('extruder_offset_x2', '0.0', float, 'machine', 'hidden').setLabel(_("Offset X"), _("The offset of your tertiary extruder compared to the primary."))
setting('extruder_offset_y2', '0.0', float, 'machine', 'hidden').setLabel(_("Offset Y"), _("The offset of your tertiary extruder compared to the primary."))
setting('extruder_offset_x3', '0.0', float, 'machine', 'hidden').setLabel(_("Offset X"), _("The offset of your forth extruder compared to the primary."))
setting('extruder_offset_y3', '0.0', float, 'machine', 'hidden').setLabel(_("Offset Y"), _("The offset of your forth extruder compared to the primary."))
setting('steps_per_e', '0', float, 'machine', 'hidden').setLabel(_("E-Steps per 1mm filament"), _("Amount of steps per mm filament extrusion. If set to 0 then this value is ignored and the value in your firmware is used."))
setting('serial_port', 'AUTO', str, 'machine', 'hidden').setLabel(_("Serial port"), _("Serial port to use for communication with the printer"))
setting('serial_port_auto', '', str, 'machine', 'hidden')
setting('serial_baud', 'AUTO', str, 'machine', 'hidden').setLabel(_("Baudrate"), _("Speed of the serial port communication\nNeeds to match your firmware settings\nCommon values are 250000, 115200, 57600"))
setting('serial_baud_auto', '', int, 'machine', 'hidden')

setting('extruder_head_size_min_x', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards X min (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 75mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_min_y', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards Y min (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 18mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_max_x', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards X max (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 18mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_max_y', '0.0', float, 'machine', 'hidden').setLabel(_("Head size towards Y max (mm)"), _("The head size when printing multiple objects, measured from the tip of the nozzle towards the outer part of the head. 35mm for an Ultimaker if the fan is on the left side."))
setting('extruder_head_size_height', '0.0', float, 'machine', 'hidden').setLabel(_("Printer gantry height (mm)"), _("The height of the gantry holding up the printer head. If an object is higher then this then you cannot print multiple objects one for one. 60mm for an Ultimaker."))

validators.warningAbove(settingsDictionary['filament_flow'], 150, "More flow then 150% is rare and usually not recommended.")
validators.warningBelow(settingsDictionary['filament_flow'], 50, "More flow then 50% is rare and usually not recommended.")
validators.warningAbove(settingsDictionary['layer_height'], lambda : (float(getProfileSetting('nozzle_size')) * 80.0 / 100.0), "Thicker layers then %.2fmm (80%% nozzle size) usually give bad results and are not recommended.")
validators.wallThicknessValidator(settingsDictionary['wall_thickness'])
validators.warningAbove(settingsDictionary['print_speed'], 150.0, "It is highly unlikely that your machine can achieve a printing speed above 150mm/s")
validators.printSpeedValidator(settingsDictionary['print_speed'])
validators.warningAbove(settingsDictionary['print_temperature'], 260.0, "Temperatures above 260C could damage your machine, be careful!")
validators.warningAbove(settingsDictionary['print_temperature2'], 260.0, "Temperatures above 260C could damage your machine, be careful!")
validators.warningAbove(settingsDictionary['print_temperature3'], 260.0, "Temperatures above 260C could damage your machine, be careful!")
validators.warningAbove(settingsDictionary['print_temperature4'], 260.0, "Temperatures above 260C could damage your machine, be careful!")
validators.warningAbove(settingsDictionary['filament_diameter'], 3.5, "Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm.")
validators.warningAbove(settingsDictionary['filament_diameter2'], 3.5, "Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm.")
validators.warningAbove(settingsDictionary['filament_diameter3'], 3.5, "Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm.")
validators.warningAbove(settingsDictionary['filament_diameter4'], 3.5, "Are you sure your filament is that thick? Normal filament is around 3mm or 1.75mm.")
validators.warningAbove(settingsDictionary['travel_speed'], 300.0, "It is highly unlikely that your machine can achieve a travel speed above 300mm/s")
validators.warningAbove(settingsDictionary['bottom_thickness'], lambda : (float(getProfileSetting('nozzle_size')) * 3.0 / 4.0), "A bottom layer of more then %.2fmm (3/4 nozzle size) usually give bad results and is not recommended.")

#Conditions for multiple extruders
settingsDictionary['print_temperature2'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['print_temperature3'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 2)
settingsDictionary['print_temperature4'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 3)
settingsDictionary['filament_diameter2'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['filament_diameter3'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 2)
settingsDictionary['filament_diameter4'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 3)
settingsDictionary['support_dual_extrusion'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
settingsDictionary['retraction_dual_amount'].addCondition(lambda : int(getMachineSetting('extruder_amount')) > 1)
#Heated bed
settingsDictionary['print_bed_temperature'].addCondition(lambda : getMachineSetting('has_heated_bed') == 'True')

#UltiGCode uses less settings, as these settings are located inside the machine instead of gcode.
settingsDictionary['print_temperature'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_temperature2'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_temperature3'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_temperature4'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter2'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter3'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_diameter4'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['filament_flow'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['print_bed_temperature'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['retraction_speed'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['retraction_amount'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')
settingsDictionary['retraction_dual_amount'].addCondition(lambda : getMachineSetting('gcode_flavor') != 'UltiGCode')

#Remove fake defined _() because later the localization will define a global _()
del _

#########################################################
## Profile and preferences functions
#########################################################

def getSubCategoriesFor(category):
	done = {}
	ret = []
	for s in settingsList:
		if s.getCategory() == category and not s.getSubCategory() in done and s.checkConditions():
			done[s.getSubCategory()] = True
			ret.append(s.getSubCategory())
	return ret

def getSettingsForCategory(category, subCategory = None):
	ret = []
	for s in settingsList:
		if s.getCategory() == category and (subCategory is None or s.getSubCategory() == subCategory) and s.checkConditions():
			ret.append(s)
	return ret

## Profile functions
def getBasePath():
	if platform.system() == "Windows":
		basePath = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
		#If we have a frozen python install, we need to step out of the library.zip
		if hasattr(sys, 'frozen'):
			basePath = os.path.normpath(os.path.join(basePath, ".."))
	else:
		basePath = os.path.expanduser('~/.cura/%s' % version.getVersion(False))
	if not os.path.isdir(basePath):
		os.makedirs(basePath)
	return basePath

def getAlternativeBasePaths():
	paths = []
	basePath = os.path.normpath(os.path.join(getBasePath(), '..'))
	for subPath in os.listdir(basePath):
		path = os.path.join(basePath, subPath)
		if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'preferences.ini')) and path != getBasePath():
			paths.append(path)
		path = os.path.join(basePath, subPath, 'Cura')
		if os.path.isdir(path) and os.path.isfile(os.path.join(path, 'preferences.ini')) and path != getBasePath():
			paths.append(path)
	return paths

def getDefaultProfilePath():
	return os.path.join(getBasePath(), 'current_profile.ini')

def loadProfile(filename):
	#Read a configuration file as global config
	profileParser = ConfigParser.ConfigParser()
	try:
		profileParser.read(filename)
	except ConfigParser.ParsingError:
		return
	global settingsList
	for set in settingsList:
		if set.isPreference():
			continue
		section = 'profile'
		if set.isAlteration():
			section = 'alterations'
		if profileParser.has_option(section, set.getName()):
			set.setValue(unicode(profileParser.get(section, set.getName()), 'utf-8', 'replace'))

def saveProfile(filename):
	#Save the current profile to an ini file
	profileParser = ConfigParser.ConfigParser()
	profileParser.add_section('profile')
	profileParser.add_section('alterations')
	global settingsList
	for set in settingsList:
		if set.isPreference() or set.isMachineSetting():
			continue
		if set.isAlteration():
			profileParser.set('alterations', set.getName(), set.getValue().encode('utf-8'))
		else:
			profileParser.set('profile', set.getName(), set.getValue().encode('utf-8'))

	profileParser.write(open(filename, 'w'))

def resetProfile():
	#Read a configuration file as global config
	global settingsList
	for set in settingsList:
		if set.isPreference():
			continue
		set.setValue(set.getDefault())

	if getMachineSetting('machine_type') == 'ultimaker':
		putProfileSetting('nozzle_size', '0.4')
		if getMachineSetting('ultimaker_extruder_upgrade') == 'True':
			putProfileSetting('retraction_enable', 'True')
	elif getMachineSetting('machine_type') == 'ultimaker2':
		putProfileSetting('nozzle_size', '0.4')
		putProfileSetting('retraction_enable', 'True')
	else:
		putProfileSetting('nozzle_size', '0.5')

def setProfileFromString(options):
	options = base64.b64decode(options)
	options = zlib.decompress(options)
	(profileOpts, alt) = options.split('\f', 1)
	global settingsDictionary
	for option in profileOpts.split('\b'):
		if len(option) > 0:
			(key, value) = option.split('=', 1)
			if key in settingsDictionary:
				if settingsDictionary[key].isProfile():
					settingsDictionary[key].setValue(value)
	for option in alt.split('\b'):
		if len(option) > 0:
			(key, value) = option.split('=', 1)
			if key in settingsDictionary:
				if settingsDictionary[key].isAlteration():
					settingsDictionary[key].setValue(value)

def getProfileString():
	p = []
	alt = []
	global settingsList
	for set in settingsList:
		if set.isProfile():
			if set.getName() in tempOverride:
				p.append(set.getName() + "=" + tempOverride[set.getName()])
			else:
				p.append(set.getName() + "=" + set.getValue())
		elif set.isAlteration():
			if set.getName() in tempOverride:
				alt.append(set.getName() + "=" + tempOverride[set.getName()])
			else:
				alt.append(set.getName() + "=" + set.getValue())
	ret = '\b'.join(p) + '\f' + '\b'.join(alt)
	ret = base64.b64encode(zlib.compress(ret, 9))
	return ret

def insertNewlines(string, every=64): #This should be moved to a better place then profile.
	lines = []
	for i in xrange(0, len(string), every):
		lines.append(string[i:i+every])
	return '\n'.join(lines)

def getPreferencesString():
	p = []
	global settingsList
	for set in settingsList:
		if set.isPreference():
			p.append(set.getName() + "=" + set.getValue())
	ret = '\b'.join(p)
	ret = base64.b64encode(zlib.compress(ret, 9))
	return ret


def getProfileSetting(name):
	if name in tempOverride:
		return tempOverride[name]
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isProfile():
		return settingsDictionary[name].getValue()
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in profile settings\n' % (name))
	return ''

def getProfileSettingFloat(name):
	try:
		setting = getProfileSetting(name).replace(',', '.')
		return float(eval(setting, {}, {}))
	except:
		return 0.0

def putProfileSetting(name, value):
	#Check if we have a configuration file loaded, else load the default.
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isProfile():
		settingsDictionary[name].setValue(value)

def isProfileSetting(name):
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isProfile():
		return True
	return False

## Preferences functions
def getPreferencePath():
	return os.path.join(getBasePath(), 'preferences.ini')

def getPreferenceFloat(name):
	try:
		setting = getPreference(name).replace(',', '.')
		return float(eval(setting, {}, {}))
	except:
		return 0.0

def getPreferenceColour(name):
	colorString = getPreference(name)
	return [float(int(colorString[1:3], 16)) / 255, float(int(colorString[3:5], 16)) / 255, float(int(colorString[5:7], 16)) / 255, 1.0]

def loadPreferences(filename):
	global settingsList
	#Read a configuration file as global config
	profileParser = ConfigParser.ConfigParser()
	try:
		profileParser.read(filename)
	except ConfigParser.ParsingError:
		return

	for set in settingsList:
		if set.isPreference():
			if profileParser.has_option('preference', set.getName()):
				set.setValue(unicode(profileParser.get('preference', set.getName()), 'utf-8', 'replace'))

	n = 0
	while profileParser.has_section('machine_%d' % (n)):
		for set in settingsList:
			if set.isMachineSetting():
				if profileParser.has_option('machine_%d' % (n), set.getName()):
					set.setValue(unicode(profileParser.get('machine_%d' % (n), set.getName()), 'utf-8', 'replace'), n)
		n += 1

	setActiveMachine(int(getPreferenceFloat('active_machine')))

def savePreferences(filename):
	global settingsList
	#Save the current profile to an ini file
	parser = ConfigParser.ConfigParser()
	parser.add_section('preference')

	for set in settingsList:
		if set.isPreference():
			parser.set('preference', set.getName(), set.getValue().encode('utf-8'))

	n = 0
	while getMachineSetting('machine_name', n) != '':
		parser.add_section('machine_%d' % (n))
		for set in settingsList:
			if set.isMachineSetting():
				parser.set('machine_%d' % (n), set.getName(), set.getValue(n).encode('utf-8'))
		n += 1
	parser.write(open(filename, 'w'))

def getPreference(name):
	if name in tempOverride:
		return tempOverride[name]
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isPreference():
		return settingsDictionary[name].getValue()
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in preferences\n' % (name))
	return ''

def putPreference(name, value):
	#Check if we have a configuration file loaded, else load the default.
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isPreference():
		settingsDictionary[name].setValue(value)
		savePreferences(getPreferencePath())
		return
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in preferences\n' % (name))

def isPreference(name):
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isPreference():
		return True
	return False

def getMachineSettingFloat(name):
	try:
		setting = getMachineSetting(name).replace(',', '.')
		return float(eval(setting, {}, {}))
	except:
		return 0.0

def getMachineSetting(name, index = None):
	if name in tempOverride:
		return tempOverride[name]
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isMachineSetting():
		return settingsDictionary[name].getValue(index)
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in machine settings\n' % (name))
	return ''

def putMachineSetting(name, value):
	#Check if we have a configuration file loaded, else load the default.
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isMachineSetting():
		settingsDictionary[name].setValue(value)
	savePreferences(getPreferencePath())

def isMachineSetting(name):
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isMachineSetting():
		return True
	return False

def checkAndUpdateMachineName():
	global _selectedMachineIndex
	name = getMachineSetting('machine_name')
	index = None
	if name == '':
		name = getMachineSetting('machine_type')
	for n in xrange(0, getMachineCount()):
		if n == _selectedMachineIndex:
			continue
		if index is None:
			if name == getMachineSetting('machine_name', n):
				index = 1
		else:
			if '%s (%d)' % (name, index) == getMachineSetting('machine_name', n):
				index += 1
	if index is not None:
		name = '%s (%d)' % (name, index)
	putMachineSetting('machine_name', name)
	putPreference('active_machine', _selectedMachineIndex)

def getMachineCount():
	n = 0
	while getMachineSetting('machine_name', n) != '':
		n += 1
	if n < 1:
		return 1
	return n

def setActiveMachine(index):
	global _selectedMachineIndex
	_selectedMachineIndex = index
	putPreference('active_machine', _selectedMachineIndex)

def removeMachine(index):
	global _selectedMachineIndex
	global settingsList
	if getMachineCount() < 2:
		return
	for n in xrange(index, getMachineCount()):
		for setting in settingsList:
			if setting.isMachineSetting():
				setting.setValue(setting.getValue(n+1), n)

	if _selectedMachineIndex >= index:
		setActiveMachine(getMachineCount() - 1)

## Temp overrides for multi-extruder slicing and the project planner.
tempOverride = {}
def setTempOverride(name, value):
	tempOverride[name] = unicode(value).encode("utf-8")
def clearTempOverride(name):
	del tempOverride[name]
def resetTempOverride():
	tempOverride.clear()

#########################################################
## Utility functions to calculate common profile values
#########################################################
def calculateEdgeWidth():
	wallThickness = getProfileSettingFloat('wall_thickness')
	nozzleSize = getProfileSettingFloat('nozzle_size')

	if wallThickness < 0.01:
		return nozzleSize
	if wallThickness < nozzleSize:
		return wallThickness

	lineCount = int(wallThickness / (nozzleSize - 0.0001))
	if lineCount == 0:
		return nozzleSize
	lineWidth = wallThickness / lineCount
	lineWidthAlt = wallThickness / (lineCount + 1)
	if lineWidth > nozzleSize * 1.5:
		return lineWidthAlt
	return lineWidth

def calculateLineCount():
	wallThickness = getProfileSettingFloat('wall_thickness')
	nozzleSize = getProfileSettingFloat('nozzle_size')

	if wallThickness < 0.01:
		return 0
	if wallThickness < nozzleSize:
		return 1

	lineCount = int(wallThickness / (nozzleSize - 0.0001))
	if lineCount < 1:
		lineCount = 1
	lineWidth = wallThickness / lineCount
	lineWidthAlt = wallThickness / (lineCount + 1)
	if lineWidth > nozzleSize * 1.5:
		return lineCount + 1
	return lineCount

def calculateSolidLayerCount():
	layerHeight = getProfileSettingFloat('layer_height')
	solidThickness = getProfileSettingFloat('solid_layer_thickness')
	if layerHeight == 0.0:
		return 1
	return int(math.ceil(solidThickness / (layerHeight - 0.0001)))

def calculateObjectSizeOffsets():
	size = 0.0

	if getProfileSetting('platform_adhesion') == 'Brim':
		size += getProfileSettingFloat('brim_line_count') * calculateEdgeWidth()
	elif getProfileSetting('platform_adhesion') == 'Raft':
		pass
	else:
		if getProfileSettingFloat('skirt_line_count') > 0:
			size += getProfileSettingFloat('skirt_line_count') * calculateEdgeWidth() + getProfileSettingFloat('skirt_gap')

	#if getProfileSetting('enable_raft') != 'False':
	#	size += profile.getProfileSettingFloat('raft_margin') * 2
	#if getProfileSetting('support') != 'None':
	#	extraSizeMin = extraSizeMin + numpy.array([3.0, 0, 0])
	#	extraSizeMax = extraSizeMax + numpy.array([3.0, 0, 0])
	return [size, size]

def getMachineCenterCoords():
	if getMachineSetting('machine_center_is_zero') == 'True':
		return [0, 0]
	return [getMachineSettingFloat('machine_width') / 2, getMachineSettingFloat('machine_depth') / 2]

#########################################################
## Alteration file functions
#########################################################
def replaceTagMatch(m):
	pre = m.group(1)
	tag = m.group(2)
	if tag == 'time':
		return pre + time.strftime('%H:%M:%S')
	if tag == 'date':
		return pre + time.strftime('%d-%m-%Y')
	if tag == 'day':
		return pre + ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][int(time.strftime('%w'))]
	if tag == 'print_time':
		return pre + '#P_TIME#'
	if tag == 'filament_amount':
		return pre + '#F_AMNT#'
	if tag == 'filament_weight':
		return pre + '#F_WGHT#'
	if tag == 'filament_cost':
		return pre + '#F_COST#'
	if pre == 'F' and tag in ['print_speed', 'retraction_speed', 'travel_speed', 'max_z_speed', 'bottom_layer_speed', 'cool_min_feedrate']:
		f = getProfileSettingFloat(tag) * 60
	elif isProfileSetting(tag):
		f = getProfileSettingFloat(tag)
	elif isPreference(tag):
		f = getProfileSettingFloat(tag)
	else:
		return '%s?%s?' % (pre, tag)
	if (f % 1) == 0:
		return pre + str(int(f))
	return pre + str(f)

def replaceGCodeTags(filename, gcodeInt):
	f = open(filename, 'r+')
	data = f.read(2048)
	data = data.replace('#P_TIME#', ('%5d:%02d' % (int(gcodeInt.totalMoveTimeMinute / 60), int(gcodeInt.totalMoveTimeMinute % 60)))[-8:])
	data = data.replace('#F_AMNT#', ('%8.2f' % (gcodeInt.extrusionAmount / 1000))[-8:])
	data = data.replace('#F_WGHT#', ('%8.2f' % (gcodeInt.calculateWeight() * 1000))[-8:])
	cost = gcodeInt.calculateCost()
	if cost is None:
		cost = 'Unknown'
	data = data.replace('#F_COST#', ('%8s' % (cost.split(' ')[0]))[-8:])
	f.seek(0)
	f.write(data)
	f.close()

### Get aleration raw contents. (Used internally in Cura)
def getAlterationFile(filename):
	if filename in tempOverride:
		return tempOverride[filename]
	global settingsDictionary
	if filename in settingsDictionary and settingsDictionary[filename].isAlteration():
		return settingsDictionary[filename].getValue()
	traceback.print_stack()
	sys.stderr.write('Error: "%s" not found in alteration settings\n' % (filename))
	return ''

def setAlterationFile(name, value):
	#Check if we have a configuration file loaded, else load the default.
	global settingsDictionary
	if name in settingsDictionary and settingsDictionary[name].isAlteration():
		settingsDictionary[name].setValue(value)
	saveProfile(getDefaultProfilePath())

### Get the alteration file for output. (Used by Skeinforge)
def getAlterationFileContents(filename, extruderCount = 1):
	prefix = ''
	postfix = ''
	alterationContents = getAlterationFile(filename)
	if getMachineSetting('gcode_flavor') == 'UltiGCode':
		return ''
	if filename == 'start.gcode':
		if extruderCount > 1:
			alterationContents = getAlterationFile("start%d.gcode" % (extruderCount))
		#For the start code, hack the temperature and the steps per E value into it. So the temperature is reached before the start code extrusion.
		#We also set our steps per E here, if configured.
		eSteps = getMachineSettingFloat('steps_per_e')
		if eSteps > 0:
			prefix += 'M92 E%f\n' % (eSteps)
		temp = getProfileSettingFloat('print_temperature')
		bedTemp = 0
		if getMachineSetting('has_heated_bed') == 'True':
			bedTemp = getProfileSettingFloat('print_bed_temperature')

		if bedTemp > 0 and not '{print_bed_temperature}' in alterationContents:
			prefix += 'M140 S%f\n' % (bedTemp)
		if temp > 0 and not '{print_temperature}' in alterationContents:
			if extruderCount > 0:
				for n in xrange(1, extruderCount):
					t = temp
					if n > 0 and getProfileSettingFloat('print_temperature%d' % (n+1)) > 0:
						t = getProfileSettingFloat('print_temperature%d' % (n+1))
					prefix += 'M104 T%d S%f\n' % (n, t)
				for n in xrange(0, extruderCount):
					t = temp
					if n > 0 and getProfileSettingFloat('print_temperature%d' % (n+1)) > 0:
						t = getProfileSettingFloat('print_temperature%d' % (n+1))
					prefix += 'M109 T%d S%f\n' % (n, t)
				prefix += 'T0\n'
			else:
				prefix += 'M109 S%f\n' % (temp)
		if bedTemp > 0 and not '{print_bed_temperature}' in alterationContents:
			prefix += 'M190 S%f\n' % (bedTemp)
	elif filename == 'end.gcode':
		if extruderCount > 1:
			alterationContents = getAlterationFile("end%d.gcode" % (extruderCount))
		#Append the profile string to the end of the GCode, so we can load it from the GCode file later.
		postfix = ';CURA_PROFILE_STRING:%s\n' % (getProfileString())
	return unicode(prefix + re.sub("(.)\{([^\}]*)\}", replaceTagMatch, alterationContents).rstrip() + '\n' + postfix).strip().encode('utf-8') + '\n'

###### PLUGIN #####

def getPluginConfig():
	try:
		return pickle.loads(str(getProfileSetting('plugin_config')))
	except:
		return []

def setPluginConfig(config):
	putProfileSetting('plugin_config', pickle.dumps(config))

def getPluginBasePaths():
	ret = []
	if platform.system() != "Windows":
		ret.append(os.path.expanduser('~/.cura/plugins/'))
	if platform.system() == "Darwin" and hasattr(sys, 'frozen'):
		ret.append(os.path.normpath(os.path.join(resources.resourceBasePath, "Cura/plugins")))
	else:
		ret.append(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'plugins')))
	return ret

def getPluginList():
	ret = []
	for basePath in getPluginBasePaths():
		for filename in glob.glob(os.path.join(basePath, '*.py')):
			filename = os.path.basename(filename)
			if filename.startswith('_'):
				continue
			with open(os.path.join(basePath, filename), "r") as f:
				item = {'filename': filename, 'name': None, 'info': None, 'type': None, 'params': []}
				for line in f:
					line = line.strip()
					if not line.startswith('#'):
						break
					line = line[1:].split(':', 1)
					if len(line) != 2:
						continue
					if line[0].upper() == 'NAME':
						item['name'] = line[1].strip()
					elif line[0].upper() == 'INFO':
						item['info'] = line[1].strip()
					elif line[0].upper() == 'TYPE':
						item['type'] = line[1].strip()
					elif line[0].upper() == 'DEPEND':
						pass
					elif line[0].upper() == 'PARAM':
						m = re.match('([a-zA-Z][a-zA-Z0-9_]*)\(([a-zA-Z_]*)(?::([^\)]*))?\) +(.*)', line[1].strip())
						if m is not None:
							item['params'].append({'name': m.group(1), 'type': m.group(2), 'default': m.group(3), 'description': m.group(4)})
					else:
						print "Unknown item in effect meta data: %s %s" % (line[0], line[1])
				if item['name'] is not None and item['type'] == 'postprocess':
					ret.append(item)
	return ret

def runPostProcessingPlugins(gcodefilename):
	pluginConfigList = getPluginConfig()
	pluginList = getPluginList()

	for pluginConfig in pluginConfigList:
		plugin = None
		for pluginTest in pluginList:
			if pluginTest['filename'] == pluginConfig['filename']:
				plugin = pluginTest
		if plugin is None:
			continue

		pythonFile = None
		for basePath in getPluginBasePaths():
			testFilename = os.path.join(basePath, pluginConfig['filename'])
			if os.path.isfile(testFilename):
				pythonFile = testFilename
		if pythonFile is None:
			continue

		locals = {'filename': gcodefilename}
		for param in plugin['params']:
			value = param['default']
			if param['name'] in pluginConfig['params']:
				value = pluginConfig['params'][param['name']]

			if param['type'] == 'float':
				try:
					value = float(value)
				except:
					value = float(param['default'])

			locals[param['name']] = value
		try:
			execfile(pythonFile, locals)
		except:
			locationInfo = traceback.extract_tb(sys.exc_info()[2])[-1]
			return "%s: '%s' @ %s:%s:%d" % (str(sys.exc_info()[0].__name__), str(sys.exc_info()[1]), os.path.basename(locationInfo[0]), locationInfo[2], locationInfo[1])
	return None
