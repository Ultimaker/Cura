__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.util import profile

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
		self.printMaterialPLA = wx.RadioButton(printMaterialPanel, -1, 'PLA', style=wx.RB_GROUP)
		self.printMaterialABS = wx.RadioButton(printMaterialPanel, -1, 'ABS')
		self.printMaterialHIPS = wx.RadioButton(printMaterialPanel, -1, 'HIPS')
		self.printMaterialDiameter = wx.TextCtrl(printMaterialPanel, -1, profile.getProfileSetting('filament_diameter'))
		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			printMaterialPanel.Show(False)
		
		self.printSupport = wx.CheckBox(self, -1, _("Print support structure"))

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
		boxsizer.Add(self.printMaterialPLA)
		boxsizer.Add(self.printMaterialABS)
		boxsizer.Add(self.printMaterialHIPS)
		boxsizer.Add(wx.StaticText(printMaterialPanel, -1, _("Diameter:")))
		boxsizer.Add(self.printMaterialDiameter)
		printMaterialPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		printMaterialPanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(printMaterialPanel, (1,0), flag=wx.EXPAND)

		sb = wx.StaticBox(self, label=_("Other:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.Add(self.printSupport)
		sizer.Add(boxsizer, (2,0), flag=wx.EXPAND)

		self.printTypeNormal.SetValue(True)
		self.printMaterialPLA.SetValue(True)

		self.printTypeHigh.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printTypeNormal.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printTypeLow.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		#self.printTypeJoris.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())

		self.printMaterialPLA.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printMaterialABS.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printMaterialHIPS.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		self.printMaterialDiameter.Bind(wx.EVT_TEXT, lambda e: self._callback())

		self.printSupport.Bind(wx.EVT_CHECKBOX, lambda e: self._callback())

	def setupSlice(self):
		put = profile.setTempOverride
		get = profile.getProfileSetting
		for setting in profile.settingsList:
			if not setting.isProfile():
				continue
			profile.setTempOverride(setting.getName(), setting.getDefault())

		if self.printSupport.GetValue():
			put('support', _("Exterior Only"))

# LulzBot Mini slice settings for use with the simple slice selection. This needs to be further modified to only be used when the Mini machine config is loaded.
		put('print_temperature', '0')
		put('print_bed_temperature', '0')
		put('retraction_speed', '25')
		put('bottom_thickness', '0.425')
		put('layer0_width_factor', '125')
		put('fan_speed', '10')
		put('fan_speed_max', '50')
		put('cool_head_lift', 'True')
		put('end.gcode', """;End GCode
	M104 T0 S0                     ;extruder heater off
	M104 T1 S0                     ;extruder heater off
	M140 S0                     ;heated bed heater off (if you have it)
	G91                                    ;relative positioning
	G1 E-1 F300                            ;retract the filament a bit before lifting the nozzle, to release some of the pressure
	G1 Z+0.5 E-5 X-20 Y-20 F{travel_speed} ;move Z up a bit and retract filament even more
	G28 X0 Y0                              ;move X/Y to min endstops, so the head is out of the way
	M84                         ;steppers off
	G90                         ;absolute positioning
	;{profile_string}""")

		if self.printMaterialHIPS.GetValue() or self.printMaterialABS.GetValue():
			put('solid_layer_thickness', '0.8')
			put('fill_density', '40')
			put('retraction_amount', '1.5')
			put('travel_speed', '175')
			put('start.gcode', """;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
	;Print time: {print_time}
	;Filament used: {filament_amount}m {filament_weight}g
	;Filament cost: {filament_cost}
	;M190 S{print_bed_temperature} ;Uncomment to add your own bed temperature line
	;M109 S{print_temperature} ;Uncomment to add your own temperature line
	G21                    ; metric values
	G90                    ; absolute positioning
	M82                    ; set extruder to absolute mode
	M107                   ; start with the fan off
	G92 E0                 ; set extruder position to 0
	M140 S110               ; get bed heating up
	G28                    ; home all
	M109 S150              ; set to cleaning temp and wait
	G1 Z150 E-45 F200      ; suck up XXmm of filament
	M109 S170              ; heat up rest of way
	G1 X45 Y178 F11520     ; move behind scraper
	G1 Z0  F1200           ; CRITICAL: set Z to height of top of scraper
	G1 X45 Y178 Z-1 F4000  ; wiping ; plunge into wipe pad
	G1 X55 Y176 Z-.5 F4000  ; wiping
	G1 X45 Y178 F4000      ; wiping
	G1 X55 Y176 F4000      ; wiping
	G1 X45 Y178 F4000      ; wiping
	G1 X55 Y176 F4000      ; wiping
	G1 X45 Y178 F4000      ; wiping
	G1 X55 Y176 F4000      ; wiping
	G1 X60 Y178 F4000      ; wiping
	G1 X80 Y176 F4000      ; wiping
	G1 X60 Y178 F4000      ; wiping
	G1 X80 Y176 F4000      ; wiping
	G1 X60 Y178 F4000      ; wiping
	G1 X90 Y176 F4000      ; wiping
	G1 X80 Y178 F4000      ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X80 Y178 F4000      ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X80 Y178 F4000      ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X110 Y178 F4000     ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X110 Y178 F4000     ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X110 Y178 F4000     ; wiping
	G1 X115 Y175 Z-1.5 F1000 ; wipe slower and bury noz in cleanish area
	G1 Z10                 ; raise z
	G28 X0 Y0              ; home x and y
	M109 S170              ; set to probing temp
	G29                    ; Probe
	G1 X5 Y15 Z10 F5000    ; get out the way
	M109 S230              ; set extruder temp and wait
	G1 Z2 E5 F200          ; extrude filament back into nozzle
	M140 S110               ; get bed temping up during first layer
	M206 X0.0 Y0.0 Z0.0    ; offset home position for fine tuning""")
		elif self.printMaterialPLA.GetValue():
			put('start.gcode', """;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
	;Print time: {print_time}
	;Filament used: {filament_amount}m {filament_weight}g
	;Filament cost: {filament_cost}
	;M190 S{print_bed_temperature} ;Uncomment to add your own bed temperature line
	;M109 S{print_temperature} ;Uncomment to add your own temperature line
	
	G21                    ; metric values
	G90                    ; absolute positioning
	M82                    ; set extruder to absolute mode
	M107                   ; start with the fan off
	G92 E0                 ; set extruder position to 0
	M140 S65               ; get bed heating up
	G28                    ; home all
	M109 S130              ; set to cleaning temp and wait
	G1 Z150 E-45 F200      ; suck up XXmm of filament
	M109 S140              ; heat up rest of way
	G1 X45 Y178 F11520     ; move behind scraper
	G1 Z0  F1200           ; CRITICAL: set Z to height of top of scraper
	G1 X45 Y178 Z-1 F4000  ; wiping ; plunge into wipe pad
	G1 X55 Y176 Z-.5 F4000  ; wiping
	G1 X45 Y178 F4000      ; wiping
	G1 X55 Y176 F4000      ; wiping
	G1 X45 Y178 F4000      ; wiping
	G1 X55 Y176 F4000      ; wiping
	G1 X45 Y178 F4000      ; wiping
	G1 X55 Y176 F4000      ; wiping
	G1 X60 Y178 F4000      ; wiping
	G1 X80 Y176 F4000      ; wiping
	G1 X60 Y178 F4000      ; wiping
	G1 X80 Y176 F4000      ; wiping
	G1 X60 Y178 F4000      ; wiping
	G1 X90 Y176 F4000      ; wiping
	G1 X80 Y178 F4000      ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X80 Y178 F4000      ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X80 Y178 F4000      ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X110 Y178 F4000     ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X110 Y178 F4000     ; wiping
	G1 X100 Y176 F4000     ; wiping
	G1 X110 Y178 F4000     ; wiping
	G1 X115 Y175 Z-1.5 F1000 ; wipe slower and bury noz in cleanish area
	G1 Z10                 ; raise z
	G28 X0 Y0              ; home x and y
	M109 S140              ; set to probing temp
	G29                    ; Probe
	G1 X5 Y15 Z10 F5000    ; get out the way
	M109 S190              ; set extruder temp and wait
	G1 Z2 E5 F200          ; extrude filament back into nozzle
	M140 S65               ; get bed temping up during first layer
	M206 X0.0 Y0.0 Z0.0    ; offset home position for fine tuning
end.gcode = M104 S0
	M140 S0                      ;heated bed heater off (if you have it)
	M107                         ; fans off
	G91                          ;relative positioning
	G1 E-1 F300                  ;retract the filament a bit before lifting the nozzle, to release some of the pressure
	G1 Z+0.5 E-5 X-20 Y-20 F3000 ;move Z up a bit and retract filament even more
	G1 X155 Y175 Z156 F10000            ;move X/Y to min endstops, so the head is out of the way
	M84                          ;steppers off
	G90                          ;absolute positioning
	;{profile_string}""")

		nozzle_size = float(get('nozzle_size'))
		if self.printMaterialHIPS.GetValue():
			put('retraction_hop', '0.6')
			put('bottom_layer_speed', '30')
			put('fan_full_height', '5')
			put('cool_min_feedrate', '45')
			if self.printTypeLow.GetValue():
				put('layer_height', '0.38')
				put('print_speed', '85')
				put('infill_speed', '115')
				put('inset0_speed', '75')
				put('insetx_speed', '80')
			if self.printTypeNormal.GetValue():
				put('layer_height', '0.25')
				put('print_speed', '65')
				put('infill_speed', '85')
				put('inset0_speed', '45')
				put('insetx_speed', '50')
			if self.printTypeHigh.GetValue():
				put('layer_height', '0.14')
				put('print_speed', '40')
				put('infill_speed', '65')
				put('inset0_speed', '30')
				put('insetx_speed', '35')
		if self.printMaterialABS.GetValue():
			put('retraction_hop', '0.6')
			put('cool_min_feedrate', '10')
			put('fan_enabled', 'False')
			if self.printTypeLow.GetValue():
				put('layer_height', '0.38')
				put('print_speed', '85')
				put('bottom_layer_speed', '30')
				put('infill_speed', '110')
				put('inset0_speed', '70')
				put('insetx_speed', '80')
				put('brim_line_count', '8')
			if self.printTypeNormal.GetValue():
				put('layer_height', '0.25')
				put('print_speed', '75')
				put('bottom_layer_speed', '25')
				put('infill_speed', '80')
				put('inset0_speed', '60')
				put('insetx_speed', '70')
			if self.printTypeHigh.GetValue():
				put('layer_height', '0.14')
				put('print_speed', '60')
				put('bottom_layer_speed', '25')
				put('infill_speed', '60')
				put('inset0_speed', '40')
				put('insetx_speed', '50')
				put('fan_full_height', '5')
				put('skirt_line_count', '4')
		if self.printMaterialPLA.GetValue():
			put('solid_Layer_thickness', '1')
			put('fill_density', '70')
			put('retraction_amount', '3')
			put('retraction_hop', '0.5')
			put('travel_speed', '150')
			put('bottom_travel_speed', '30')
			put('fan_full_height', '1')
			put('cool_min_feedrate', '15')
			put('skirt_line_count', '2')
			if self.printTypeLow.GetValue():
				put('layer_height', '0.38')
				put('print_speed', '90')
				put('infill_speed', '125')
				put('inset0_speed', '75')
				put('insetx_speed', '85')
			if self.printTypeNormal.GetValue():
				put('layer_height', '0.25')
				put('print_speed', '70')
				put('infill_speed', '95')
				put('inset0_speed', '65')
				put('insetx_speed', '75')
			if self.printTypeHigh.GetValue():
				pass

		nozzle_size = float(get('nozzle_size'))
		put('filament_diameter', self.printMaterialDiameter.GetValue())
		put('plugin_config', '')

	def updateProfileToControls(self):
		pass
