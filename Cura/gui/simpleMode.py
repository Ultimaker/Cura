__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.util import profile
import cPickle as pickle

class simpleModePanel(wx.Panel):
	"Main user interface window for Quickprint mode"
	def __init__(self, parent, callback):
		super(simpleModePanel, self).__init__(parent)
		self._callback = callback

		#toolsMenu = wx.Menu()
		#i = toolsMenu.Append(-1, 'Switch to Normal mode...')
		#self.Bind(wx.EVT_MENU, self.OnNormalSwitch, i)
		#self.menubar.Insert(1, toolsMenu, 'Normal mode')

		printTypePanel = wx.Panel(self)
		self.printTypeHigh = wx.RadioButton(printTypePanel, -1, _("High quality print"), style=wx.RB_GROUP)
		self.printTypeNormal = wx.RadioButton(printTypePanel, -1, _("Normal quality print"))
		self.printTypeLow = wx.RadioButton(printTypePanel, -1, _("Fast low quality print"))
		self.printTypeJoris = wx.RadioButton(printTypePanel, -1, _("Thin walled cup or vase"))
		self.printTypeJoris.Hide()

		printMaterialPanel = wx.Panel(self)
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_5' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_4':
			self.printMaterialHIPS = wx.RadioButton(printMaterialPanel, -1, _('HIPS'), style=wx.RB_GROUP)
			self.printMaterialABS = wx.RadioButton(printMaterialPanel, -1, _('ABS'))
		else:
			self.printMaterialABS = wx.RadioButton(printMaterialPanel, -1, _('ABS'), style=wx.RB_GROUP)
		self.printMaterialPLA = wx.RadioButton(printMaterialPanel, -1, _('PLA'))
		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			printMaterialPanel.Show(False)
		
		self.printSupport = wx.CheckBox(self, -1, _("Print support structure"))
		self.printBrim = wx.CheckBox(self, -1, _("Print Brim"))

		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)

		sb = wx.StaticBox(printTypePanel, label=_("Select a quickprint profile:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.Add(self.printTypeHigh)
		boxsizer.Add(self.printTypeNormal)
		boxsizer.Add(self.printTypeLow)
		boxsizer.Add(self.printTypeJoris, border=5, flag=wx.TOP)
		printTypePanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		printTypePanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(printTypePanel, (0,0), flag=wx.EXPAND)

		sb = wx.StaticBox(printMaterialPanel, label=_("Material:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_5' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_4':
			boxsizer.Add(self.printMaterialHIPS)
		boxsizer.Add(self.printMaterialABS)
		boxsizer.Add(self.printMaterialPLA)
		printMaterialPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		printMaterialPanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(printMaterialPanel, (1,0), flag=wx.EXPAND)

		sb = wx.StaticBox(self, label=_("Other:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.Add(self.printSupport)
		boxsizer.Add(self.printBrim)
		sizer.Add(boxsizer, (2,0), flag=wx.EXPAND)

		self.printTypeNormal.SetValue(True)
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ':
			self.printMaterialHIPS.SetValue(True)
		else:
			self.printMaterialPLA.SetValue(True)

		self.printTypeHigh.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printTypeNormal.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printTypeLow.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		#self.printTypeJoris.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())

		self.printMaterialPLA.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printMaterialABS.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_4':
			self.printMaterialHIPS.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())

		self.printSupport.Bind(wx.EVT_CHECKBOX, lambda e: self._callback())
		self.printBrim.Bind(wx.EVT_CHECKBOX, lambda e: self._callback())

		self.loadSettings()

	def getSavedSettings(self):
		try:
			return pickle.loads(str(profile.getProfileSetting('simpleModeSettings')))
		except:
			return {}

	def loadSettings(self):
		settings = self.getSavedSettings()
		for item in settings.keys():
			if hasattr(self, item):
				getattr(self, item).SetValue(settings[item])

	def saveSettings(self):
		settings = {}
		settingItems = ['printTypeHigh', 'printTypeNormal', 'printTypeLow', 'printTypeJoris',
						'printMaterialHIPS', 'printMaterialABS', 'printMaterialPLA',
						'printSupport', 'printBrim']

		for item in settingItems:
			if hasattr(self, item):
				settings[item] = getattr(self, item).GetValue()

		profile.putProfileSetting('simpleModeSettings', pickle.dumps(settings))

	def setupSlice(self):
		self.saveSettings()
		put = profile.setTempOverride
		get = profile.getProfileSetting
		for setting in profile.settingsList:
			if not setting.isProfile():
				continue
			profile.setTempOverride(setting.getName(), setting.getDefault())

# LulzBot Mini slice settings for use with the simple slice selection.
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini':
			put('filament_diameter', '2.85')
			put('nozzle_size', '0.5')
			put('wall_thickness', '1')
			put('fill_density', '20')
			put('retraction_speed', '10')
			put('retraction_hop', '0.1')
			put('bottom_thickness', '0.425')
			put('layer0_width_factor', '125')
			put('travel_speed', '175')
			put('skirt_minimal_length', '250')
			put('brim_line_count', '10')
			put('raft_airgap', '0.5')
			put('bottom_layer_speed', '15')
			put('fan_full_height', '0.5')
			put('retraction_minimal_extrusion', '0.005')
			if self.printSupport.GetValue():
				put('support', _("Everywhere"))
				put('support_type', 'Lines')
				put('support_angle', '45')
				put('support_fill_rate', '30')
				put('support_xy_distance', '0.7')
				put('support_z_distance', '0.05')
			if self.printBrim.GetValue():
				put('platform_adhesion', 'Brim')
			if self.printMaterialHIPS.GetValue() or self.printMaterialABS.GetValue():
				put('print_temperature', '240')
				put('print_bed_temperature', '110')
				put('solid_layer_thickness', '0.8')
				put('retraction_amount', '1')
				put('fan_speed', '40')
				put('start.gcode', """;This Gcode has been generated specifically for the LulzBot Mini
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Filament Diameter: {filament_diameter}
;Nozzle Size: {nozzle_size}
G21                          ; metric values
G90                          ; absolute positioning
M82                          ; set extruder to absolute mode
M107                         ; start with the fan off
G92 E0                       ; set extruder position to 0
M140 S110                    ; get bed heating up
G28                          ; home all
M109 S150                    ; set to cleaning temp and wait
G1 Z150 E-30 F75             ; suck up XXmm of filament
M109 S170                    ; heat up rest of way
G1 X45 Y174 F11520           ; move behind scraper
G1 Z0  F1200                 ; CRITICAL: set Z to height of top of scraper
G1 X45 Y174 Z-.5 F4000       ; wiping ; plunge into wipe pad
G1 X55 Y172 Z-.5 F4000       ; wiping
G1 X45 Y174 Z0 F4000         ; wiping
G1 X55 Y172 F4000            ; wiping
G1 X45 Y174 F4000            ; wiping
G1 X55 Y172 F4000            ; wiping
G1 X45 Y174 F4000            ; wiping
G1 X55 Y172 F4000            ; wiping
G1 X60 Y174 F4000            ; wiping
G1 X80 Y172 F4000            ; wiping
G1 X60 Y174 F4000            ; wiping
G1 X80 Y172 F4000            ; wiping
G1 X60 Y174 F4000            ; wiping
G1 X90 Y172 F4000            ; wiping
G1 X80 Y174 F4000            ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X80 Y174 F4000            ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X80 Y174 F4000            ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X110 Y174 F4000           ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X110 Y174 F4000           ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X110 Y174 F4000           ; wiping
G1 X115 Y172 Z-0.5 F1000     ; wipe slower and bury noz in cleanish area
G1 Z10                       ; raise z
G28 X0 Y0                    ; home x and y
M109 S170                    ; set to probing temp
M204 S300                    ; set accel for probing
G29                          ; Probe
M204 S2000                   ; set accel back to normal
G1 X5 Y15 Z10 F5000          ; get out the way
M400                         ; clear buffer
G4 S1                        ; pause
M109 S{print_temperature}    ; set extruder temp and wait
G4 S25                       ; wait for bed to temp up
G1 Z2 E0 F75                 ; extrude filament back into nozzle
M140 S{print_bed_temperature}; get bed temping up during first layer
""")
				put('end.gcode', """
M400
M104 S0                         ; Hotend off
M140 S0                         ; heated bed heater off (if you have it)
M107                            ; fans off
G92 E0                          ; set extruder to 0
G1 E-3 F300                     ; retract a bit to relieve pressure
G1 X5 Y5 Z156 F10000            ; move to cooling positioning
M190 R60                        ; wait for bed to cool
M140 S0                         ; Turn off bed temp
G1 X145 Y175 Z156 F1000         ; move to cooling positioning
M84                             ; steppers off
G90                             ; absolute positioning
;{profile_string}
""")
				if self.printMaterialHIPS.GetValue():
					put('fan_speed_max', '50')
					if self.printTypeLow.GetValue():
						put('layer_height', '0.38')
						put('print_speed', '50')
						put('infill_speed', '70')
						put('inset0_speed', '40')
						put('insetx_speed', '45')
						put('cool_min_layer_time', '15')
						put('cool_min_feedrate', '10')
					if self.printTypeNormal.GetValue():
						put('layer_height', '0.25')
						put('print_speed', '50')
						put('infill_speed', '60')
						put('inset0_speed', '30')
						put('insetx_speed', '35')
						put('cool_min_layer_time', '15')
						put('cool_min_feedrate', '10')
					if self.printTypeHigh.GetValue():
						put('layer_height', '0.18')
						put('print_speed', '30')
						put('infill_speed', '30')
						put('inset0_speed', '20')
						put('insetx_speed', '25')
						put('cool_min_layer_time', '20')
						put('cool_min_feedrate', '5')
				if self.printMaterialABS.GetValue():
					put('fan_speed_max', '60')
					if self.printTypeLow.GetValue():
						put('layer_height', '0.38')
						put('print_speed', '85')
						put('infill_speed', '60')
						put('inset0_speed', '50')
						put('insetx_speed', '55')
						put('cool_min_feedrate', '10')
					if self.printTypeNormal.GetValue():
						put('layer_height', '0.25')
						put('print_speed', '50')
						put('infill_speed', '55')
						put('inset0_speed', '45')
						put('insetx_speed', '50')
						put('cool_min_feedrate', '10')
					if self.printTypeHigh.GetValue():
						put('layer_height', '0.18')
						put('print_speed', '50')
						put('infill_speed', '40')
						put('inset0_speed', '30')
						put('insetx_speed', '35')
						put('cool_min_feedrate', '5')
			elif self.printMaterialPLA.GetValue():
				put('print_temperature', '205')
				put('print_bed_temperature', '60')
				put('solid_layer_thickness', '1')
				put('print_speed', '50')
				put('retraction_amount', '1.5')
				put('bottom_layer_speed', '15')
				put('cool_min_layer_time', '20')
				put('fan_speed', '75')
				put('fan_speed_max', '100')
				put('start.gcode', """;This Gcode has been generated specifically for the LulzBot Mini
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Filament Diameter: {filament_diameter}
;Nozzle Size: {nozzle_size}
G21                          ; metric values
G90                          ; absolute positioning
M82                          ; set extruder to absolute mode
M107                         ; start with the fan off
G92 E0                       ; set extruder position to 0
M140 S{print_bed_temperature}; get bed heating up
G28                          ; home all
M109 S140                    ; set to cleaning temp and wait
G1 Z150 E-30 F75             ; suck up XXmm of filament
M109 S140                    ; heat up rest of way
G1 X45 Y174 F11520           ; move behind scraper
G1 Z0  F1200                 ; CRITICAL: set Z to height of top of scraper
G1 X45 Y174 Z-.5 F4000       ; wiping ; plunge into wipe pad
G1 X55 Y172 Z-.5 F4000       ; wiping
G1 X45 Y174 Z0 F4000         ; wiping
G1 X55 Y172 F4000            ; wiping
G1 X45 Y174 F4000            ; wiping
G1 X55 Y172 F4000            ; wiping
G1 X45 Y174 F4000            ; wiping
G1 X55 Y172 F4000            ; wiping
G1 X60 Y174 F4000            ; wiping
G1 X80 Y172 F4000            ; wiping
G1 X60 Y174 F4000            ; wiping
G1 X80 Y172 F4000            ; wiping
G1 X60 Y174 F4000            ; wiping
G1 X90 Y172 F4000            ; wiping
G1 X80 Y174 F4000            ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X80 Y174 F4000            ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X80 Y174 F4000            ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X110 Y174 F4000           ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X110 Y174 F4000           ; wiping
G1 X100 Y172 F4000           ; wiping
G1 X110 Y174 F4000           ; wiping
G1 X115 Y172 Z-0.5 F1000     ; wipe slower and bury noz in cleanish area
G1 Z10                       ; raise z
G28 X0 Y0                    ; home x and y
M109 S140                    ; set to probing temp
M204 S300                    ; Set probing acceleration
G29                          ; Probe
M204 S2000                   ; Restore standard acceleration
G1 X5 Y15 Z10 F5000          ; get out the way
G4 S1                        ; pause
M400                         ; clear buffer
M109 S{print_temperature}    ; set extruder temp and wait
G4 S15                       ; wait for bed to temp up
G1 Z2 E0 F75                 ; extrude filament back into nozzle
M140 S{print_bed_temperature}; get bed temping up during first layer
""")
				put('end.gcode', """
M400
M104 S0                                      ; hotend off
M140 S0                                      ; heated bed heater off (if you have it)
M107                                         ; fans off
G92 E5                                       ; set extruder to 5mm for retract on print end
G1 X5 Y5 Z156 E0 F10000                      ; move to cooling positioning
M190 R50                                     ; wait for bed to cool
M104 S0                                      ;
G1 X145 Y175 Z156 F1000                      ; move to cooling positioning
M84                                          ; steppers off
G90                                          ; absolute positioning
;{profile_string}
""")
				if self.printTypeLow.GetValue():
					put('layer_height', '0.38')
					put('cool_min_feedrate', '10')
					put('infill_speed', '40')
					put('inset0_speed', '30')
					put('insetx_speed', '35')
				if self.printTypeNormal.GetValue():
					put('layer_height', '0.25')
					put('cool_min_feedrate', '10')
					put('infill_speed', '40')
					put('inset0_speed', '30')
					put('insetx_speed', '35')
				if self.printTypeHigh.GetValue():
					put('layer_height', '0.14')
					put('cool_min_feedrate', '5')
					put('infill_speed', '30')
					put('inset0_speed', '25')
					put('insetx_speed', '27')
### LulzBot TAZ 5 slice settings for use with the simple slice selection.
		if profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_5':
			put('wall_thickness', '1.05')
			put('retraction_speed', '10')
			put('retraction_hop', '0.1')
			put('layer0_width_factor', '125')
			put('travel_speed', '175')
			put('bottom_layer_speed', '15')
			put('skirt_minimal_length', '250')
			put('fan_full_height', '0.5')
			put('brim_line_count', '10')
			put('print_temperature', '0')
			put('print_bed_temperature', '0')
			if self.printSupport.GetValue():
				put('support', _("Everywhere"))
				put('support_type', 'Lines')
				put('support_angle', '45')
				put('support_fill_rate', '30')
				put('support_xy_distance', '0.7')
				put('support_z_distance', '0.05')
			put('start.gcode', """;Sliced at: {day} {date} {time} for use with the LulzBot TAZ 5
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
G21                     ;metric values
G90                     ;absolute positioning
M82                     ;set extruder to absolute mode
M107                    ;start with the fan off
G28 X0 Y0               ;move X/Y to min endstops
G28 Z0                  ;move Z to min endstops
G1 Z15.0 F{travel_speed};move the platform down 15mm
G92 E0                  ; zero the extruded length
G1 F200 E0              ; extrude 3mm of feed stock
G92 E0                  ; zero the extruded length again
G1 F{travel_speed}      ; set travel speed
M203 X192 Y208 Z3       ; speed limits
M117 Printing...        ; send message to LCD""")
			put('end.gcode', """M400                           ; wait for buffer to clear
M104 S0                        ; hotend off
M140 S0                        ; heated bed heater off (if you have it)
M107                           ; fans off
G91                            ; relative positioning
G1 E-1 F300                    ; retract the filament a bit before lifting the nozzle, to release some of the pressure
G1 Z+0.5 E-5 X-20 Y-20 F3000   ; move Z up a bit and retract filament even more
G90                            ; absolute positioning
G1 X0 Y250                     ; move to cooling position
M84                            ; steppers off
G90                            ; absolute positioning
M117 TAZ Ready.
;{profile_string}""")
			if self.printMaterialHIPS.GetValue() or self.printMaterialABS.GetValue():
				put('retraction_amount', '1')
				put('fan_speed', '40')
			if self.printMaterialHIPS.GetValue() or self.printMaterialPLA.GetValue():
				put('raft_airgap', '0.5')
			if self.printMaterialHIPS:
				put('fan_speed_max', '50')
				put('cool_min_layer_time', '20')
				if self.printTypeLow.GetValue():
					put('layer_height', '0.28')
					put('solid_layer_thickness', '0.84')
					put('infill_speed', '70')
					put('inset0_speed', '40')
					put('insetx_speed', '45')
				if self.printTypeNormal.GetValue():
					put('layer_height', '0.22')
					put('solid_layer_thickness', '0.88')
					put('infill_speed', '50')
					put('inset0_speed', '30')
					put('insetx_speed', '35')
				if self.printTypeHigh.GetValue():
					put('layer_height', '0.14')
					put('solid_layer_thickness', '0.7')
					put('infill_speed', '30')
					put('inset0_speed', '20')
					put('insetx_speed', '25')
			if self.printMaterialABS.GetValue():
				put('fan_speed_max', '60')
				put('raft_airgap', '0.35')
				if self.printTypeLow.GetValue():
					put('layer_height', '0.28')
					put('solid_layer_thickness', '0.84')
					put('infill_speed', '60')
					put('inset0_speed', '50')
					put('insetx_speed', '55')
					put('cool_min_layer_time', '15')
				if self.printTypeNormal.GetValue():
					put('layer_height', '0.22')
					put('solid_layer_thickness', '0.88')
					put('infill_speed', '55')
					put('inset0_speed', '45')
					put('insetx_speed', '50')
					put('cool_min_layer_time', '15')
				if self.printTypeHigh.GetValue():
					put('layer_height', '0.16')
					put('solid_layer_thickness', '0.74')
					put('infill_speed', '40')
					put('inset0_speed', '30')
					put('insetx_speed', '35')
					put('cool_min_layer_time', '20')
			if self.printMaterialPLA.GetValue():
				put('retraction_amount', '1.5')
				put('fan_speed', '75')
				put('fan_speed_max', '100')
				if self.printTypeLow.GetValue():
					put('layer_height', '0.28')
					put('solid_layer_thickness', '0.84')
					put('infill_speed', '80')
					put('inset0_speed', '60')
					put('insetx_speed', '70')
					put('cool_min_layer_time', '15')
					put('cool_min_feedrate', '15')
				if self.printTypeNormal.GetValue():
					put('layer_height', '0.21')
					put('solid_layer_thickness', '0.84')
					put('infill_speed', '60')
					put('inset0_speed', '50')
					put('insetx_speed', '55')
					put('cool_min_layer_time', '15')
					put('cool_min_feedrate', '10')
				if self.printTypeHigh.GetValue():
					put('layer_height', '0.14')
					put('solid_layer_thickness', '0.7')
					put('infill_speed', '50')
					put('inset0_speed', '40')
					put('insetx_speed', '45')
					put('cool_min_layer_time', '20')
					put('cool_min_feedrate', '5')

### LulzBot TAZ 4 slice settings for use with the simple slice selection.
		if profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_4':
			put('filament_diameter', '2.85')
			put('nozzle_size', '0.35')
			put('wall_thickness', '1.05')
			put('solid_layer_thickness', '0.84')
			put('retraction_amount', '1.5')
			put('layer0_width_factor', '125')
			put('print_temperature', '0')
			put('print_bed_temperature', '0')
			put('bottom_layer_speed', '30')
			put('travel_speed', '175')
			put('cool_min_layer_time', '15')
			put('retraction_speed', '25')
			put('start.gcode', """;This Gcode has been generated specifically for the LulzBot TAZ 4
	;Sliced at: {day} {date} {time}
	;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
	;Filament Diameter: {filament_diameter}
	;Print time: {print_time}
	;M190 S{print_bed_temperature} ;Uncomment to add your own bed temperature line
	;M109 S{print_temperature} ;Uncomment to add your own temperature line
	G21        ;metric values
	G90        ;absolute positioning
	M82        ;set extruder to absolute mode
	M107       ;start with the fan off
	G28 X0 Y0  ;move X/Y to min endstops
	G28 Z0     ;move Z to min endstops
	G1 Z15.0 F{travel_speed} ;move the platform down 15mm
	G92 E0                  ;zero the extruded length
	G1 F200 E0              ;extrude 3mm of feed stock
	G92 E0                  ;zero the extruded length again
	G1 F{travel_speed}
	M203 X192 Y208 Z3 ;speed limits""")
			put('end.gcode', """= M400
	M104 S0                                        ; Hotend off
	M140 S0                                        ;heated bed heater off (if you have it)
	M107                                             ; fans off
	G91                                                ;relative positioning
	G1 E-1 F300                                  ;retract the filament a bit before lifting the nozzle, to release some of the pressure
	G1 Z+0.5 E-5 X-20 Y-20 F3000    ;move Z up a bit and retract filament even more
	M84                                                 ;steppers off
	G90                                                 ;absolute positioning
	;{profile_string}""")
			if self.printSupport.GetValue():
				put('support', _("Everywhere"))
				put('support_type', 'Lines')
				put('support_angle', '45')
				put('support_fill_rate', '30')
				put('support_xy_distance', '0.7')
				put('support_z_distance', '0.05')
			if self.printBrim.GetValue():
				put('platform_adhesion', 'Brim')
			if self.printMaterialHIPS.GetValue() or self.printMaterialABS.GetValue():
				if self.printMaterialHIPS.GetValue():
					if self.printTypeLow.GetValue():
						put('layer_height', '0.28')
						put('print_speed', '120')
						put('retraction_hop', '0.1')
						put('inset0_speed', '80')
						put('insetx_speed', '100')
						put('fan_full_height', '1')
						put('fan_speed', '25')
						put('fan_speed_max', '30')
					if self.printTypeNormal.GetValue():
						put('layer_height', '0.21')
						put('print_speed', '100')
						put('inset0_speed', '60')
						put('insetx_speed', '80')
						put('skirt_minimal_length', '250')
						put('fan_full_height', '0.35')
						put('fan_speed', '50')
						put('fan_speed_max', '50')
					if self.printTypeHigh.GetValue():
						put('layer_height', '0.14')
						put('print_speed', '60')
						put('inset0_speed', '40')
						put('insetx_speed', '50')
						put('fan_full_height', '0.56')
						put('fan_speed', '50')
						put('fan_speed_max', '60')
						put('cool_min_feedrate', '8')
				if self.printMaterialABS.GetValue():
					if self.printTypeLow.GetValue():
						put('layer_height', '0.28')
						put('print_speed', '120')
						put('retraction_hop', '0.1')
						put('inset0_speed', '80')
						put('insetx_speed', '100')
						put('fan_full_height', '5')
						put('fan_speed', '25')
						put('fan_speed_max', '30')
					if self.printTypeNormal.GetValue():
						put('layer_height', '0.21')
						put('print_speed', '100')
						put('inset0_speed', '60')
						put('insetx_speed', '80')
						put('fan_speed', '25')
						put('fan_speed_max', '25')
						put('fill_overlap', '5')
					if self.printTypeHigh.GetValue():
						put('layer_height', '0.14')
						put('print_speed', '60')
						put('retraction_hop', '0.1')
						put('inset0_speed', '40')
						put('insetx_speed', '50')
						put('fan_full_height', '5')
						put('fan_speed', '40')
						put('fan_speed_max', '75')
			elif self.printMaterialPLA.GetValue():
				if self.printTypeLow.GetValue():
					put('layer_height', '0.28')
					put('print_speed', '120')
					put('retraction_hop', '0.1')
					put('inset0_speed', '80')
					put('insetx_speed', '100')
					put('skirt_minimal_length', '250')
					put('fan_full_height', '1')
					put('fan_speed', '75')
					put('cool_min_feedrate', '15')
					put('fill_overlap', '0')
				if self.printTypeNormal.GetValue():
					put('layer_height', '0.21')
					put('print_speed', '100')
					put('retraction_hop', '0.1')
					put('inset0_speed', '60')
					put('insetx_speed', '80')
					put('skirt_minimal_length', '250')
					put('fan_full_height', '1')
					put('fan_speed', '75')
					put('cool_min_feedrate', '15')
				if self.printTypeHigh.GetValue():
					put('layer_height', '0.14')
					put('print_speed', '60')
					put('inset0_speed', '40')
					put('insetx_speed', '50')
					put('skirt_minimal_length', '0')
					put('fan_full_height', '0.28')
					put('fill_overlap', '10')
		elif not profile.getMachineSetting('machine_type') == 'lulzbot_mini' and not profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_5' and not profile.getMachineSetting('machine_type') == 'lulzbot_TAZ_4':
			nozzle_size = float(get('nozzle_size'))
			if self.printBrim.GetValue():
				put('platform_adhesion', 'Brim')
				put('brim_line_count', '10')
			if self.printTypeNormal.GetValue():
				put('wall_thickness', nozzle_size * 2.0)
				put('layer_height', '0.10')
				put('fill_density', '20')
			elif self.printTypeLow.GetValue():
				put('wall_thickness', nozzle_size * 2.5)
				put('layer_height', '0.20')
				put('fill_density', '10')
				put('print_speed', '60')
				put('cool_min_layer_time', '3')
				put('bottom_layer_speed', '30')
			elif self.printTypeHigh.GetValue():
				put('wall_thickness', nozzle_size * 2.0)
				put('layer_height', '0.06')
				put('fill_density', '20')
				put('bottom_layer_speed', '15')
			elif self.printTypeJoris.GetValue():
				put('wall_thickness', nozzle_size * 1.5)
			if self.printSupport.GetValue():
				put('support', _("Exterior Only"))
			put('filament_diameter', '2.85')
			if self.printMaterialPLA.GetValue():
				pass
			if self.printMaterialABS.GetValue():
				put('print_bed_temperature', '100')
				put('platform_adhesion', 'Brim')
				put('filament_flow', '107')
				put('print_temperature', '245')

	def updateProfileToControls(self):
		pass
