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
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ':
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
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ':
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
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini' or profile.getMachineSetting('machine_type') == 'lulzbot_TAZ':
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

# LulzBot Mini slice settings for use with the simple slice selection.
		if profile.getMachineSetting('machine_type') == 'lulzbot_mini':
			put('fill_density', '30')
			put('print_temperature', '0')
			put('print_bed_temperature', '0')
			put('retraction_speed', '25')
			put('retraction_hop', '0.1')
			put('bottom_thickness', '0.425')
			put('layer0_width_factor', '125')
			put('cool_min_layer_time', '15')
			put('cool_head_lift', 'True')
			put('end.gcode', """;End GCode
	M400
	M104 S0                                        ; Hotend off
	M140 S0                                        ; heated bed heater off (if you have it)
	M107                                              ; fans off
	G92 E0                                           ; set extruder to 0
	G1 E-3 F300                                   ; retract a bit to relieve pressure
	G1 X5 Y5 Z156 F10000                 ; move to cooling positioning
	M190 R60                                       ; wait for bed to cool
	G1 X145 Y175 Z156 F1000         ; move to cooling positioning
	M84                                                 ; steppers off
	G90                                                 ; absolute positioning
	;{profile_string}""")

			if self.printMaterialHIPS.GetValue() or self.printMaterialABS.GetValue():
				put('solid_layer_thickness', '0.8')
				put('retraction_amount', '1.5')
				put('travel_speed', '175')
				put('fan_speed_max', '75')
				put('start.gcode', """;This Gcode has been generated specifically for the LulzBot Mini
	;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
	;Print time: {print_time}
	;Filament used: {filament_amount}m {filament_weight}g
	;Filament cost: {filament_cost}
	;M190 S{print_bed_temperature} ;Uncomment to add your own bed temperature line
	;M109 S{print_temperature} ;Uncomment to add your own temperature line
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
	M109 S230                    ; set extruder temp and wait
	G4 S25                       ; wait for bed to temp up
	G1 Z2 E0 F75                 ; extrude filament back into nozzle
	M140 S110                    ; get bed temping up during first layer""")
				if self.printMaterialHIPS.GetValue():
					put('bottom_layer_speed', '30')
					put('fan_full_height', '2')
					put('fan_speed', '45')
					put('cool_min_feedrate', '45')
					put('brim_line_count', '10')
					put('raft_airgap', '0.5')
					put('plugin_config', """(lp1
	(dp2
	S'params'
	p3
	(dp4
	S'targetL'
	p5
	V
	sS'extruderTwo'
	p6
	V
	sS'flowrateTwo'
	p7
	V
	sS'targetZ'
	p8
	V2
	sS'flowrate'
	p9
	V
	sS'fanSpeed'
	p10
	V
	sS'platformTemp'
	p11
	V85
	p12
	sS'speed'
	p13
	V
	sS'flowrateOne'
	p14
	V
	sS'extruderOne'
	p15
	V
	ssS'filename'
	p16
	S'TweakAtZ.py'
	p17
	sa.""")
					if self.printTypeLow.GetValue():
						put('layer_height', '0.38')
						put('print_speed', '85')
						put('infill_speed', '110')
						put('inset0_speed', '70')
						put('insetx_speed', '80')
					if self.printTypeNormal.GetValue():
						put('layer_height', '0.25')
						put('print_speed', '65')
						put('infill_speed', '85')
						put('inset0_speed', '45')
						put('insetx_speed', '50')
						put('skirt_minimal_length', '200')
					if self.printTypeHigh.GetValue():
						put('layer_height', '0.14')
						put('print_speed', '30')
						put('infill_speed', '50')
						put('inset0_speed', '20')
						put('insetx_speed', '25')
				if self.printMaterialABS.GetValue():
					put('cool_min_feedrate', '10')
					put('fan_enabled', 'False')
					put('fan_full_height', '5')
					put('fan_speed', '40')
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

			elif self.printMaterialPLA.GetValue():
				put('solid_layer_thickness', '1')
				put('retraction_amount', '3')
				put('skirt_minimal_length', '250')
				put('skirt_line_count', '3')
				put('fan_full_height', '1')
				put('fan_speed', '75')
				put('fan_speed_max', '100')
				put('cool_min_feedrate', '15')
				put('brim_line_count', '2')
				put('start.gcode', """;LulzBot Mini
	;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
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
				put("end.gcode", """M400
	M104 S0                                        ; Hotend off
	M140 S0                                        ; heated bed heater off (if you have it)
	M107                                              ; fans off
	G92 E0                                           ; set extruder to 0
	G1 E-3 F300                                   ; retract a bit to relieve pressure
	G1 X5 Y5 Z156 F10000                 ; move to cooling positioning
	M190 R60                                       ; wait for bed to cool
	G1 X145 Y175 Z156 F1000         ; move to cooling positioning
	M84                                                 ; steppers off
	G90                                                 ; absolute positioning
	;{profile_string}""")
				if self.printTypeLow.GetValue():
					put('layer_height', '0.38')
					put('print_speed', '90')
					put('infill_speed', '115')
					put('inset0_speed', '75')
					put('insetx_speed', '85')
				if self.printTypeNormal.GetValue():
					put('layer_height', '0.25')
					put('print_speed', '50')
					put('infill_speed', '95')
					put('inset0_speed', '65')
					put('insetx_speed', '75')
					put('raft_airgap', '0.5')
				if self.printTypeHigh.GetValue():
					put('layer_height', '0.14')
					put('print_speed', '30')
					put('bottom_layer_speed', '25')
					put('infill_speed', '75')
					put('inset0_speed', '45')
					put('insetx_speed', '55')
					put('raft_airgap', '0.5')					
			nozzle_size = float(get('nozzle_size'))
			put('filament_diameter', self.printMaterialDiameter.GetValue())
			put('plugin_config', '')
### LulzBot TAZ slice settings for use with the simple slice selection.
		if profile.getMachineSetting('machine_type') == 'lulzbot_TAZ':
			put('nozzle_size', '0.35')
			put('print_temperature', '0')
			put('print_bed_temperature', '0')
			put('start.gcode', """;Sliced at: {day} {date} {time}
	;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
	;Print time: {print_time}
	;Filament used: {filament_amount}m {filament_weight}g
	;Filament cost: {filament_cost}
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
			if self.printMaterialHIPS.GetValue() or self.printMaterialABS.GetValue():
				put('retraction_speed', '25')
				put('retraction_amount', '1.5')
				put('layer0_width_factor', '125')
				put('travel_speed', '175')
				if self.printMaterialHIPS.GetValue():
					put('bottom_layer_speed', '30')
					if self.printTypeLow.GetValue():
						put('layer_height', '0.28')
						put('solid_layer_thickness', '0.8')
						put('print_speed', '130')
						put('retraction_hop', '0.1')
						put('inset0_speed', '70')
						put('insetx_speed', '100')
						put('cool_min_layer_time', '15')
						put('fan_full_height', '1')
						put('fan_speed', '25')
						put('fan_speed_max', '30')
						put('brim_line_count', '8')
					if self.printTypeNormal.GetValue():
						put('layer_height', '0.21')
						put('wall_thickness', '1.05')
						put('solid_layer_thickness', '0.63')
						put('print_speed', '65')
						put('infill_speed', '85')
						put('inset0_speed', '45')
						put('insetx_speed', '50')
						put('skirt_minimal_length', '250')
						put('fan_full_height', '0.35')
						put('fan_speed', '50')
						put('fan_speed_max', '50')
					if self.printTypeHigh.GetValue():
						put('layer_height', '0.14')
						put('wall_thickness', '0.56')
						put('solid_layer_thickness', '0.98')
						put('fill_density', '40')
						put('print_speed', '40')
						put('infill_speed', '65')
						put('inset0_speed', '25')
						put('insetx_speed', '45')
						put('cool_min_layer_time', '10')
						put('fan_full_height', '0.56')
						put('fan_speed', '50')
						put('fan_speed_max', '60')
						put('cool_min_feedrate', '8')
				if self.printMaterialABS.GetValue():
					put('cool_min_layer_time', '15')
					if self.printTypeLow.GetValue():
						put('layer_height', '0.28')
						put('solid_layer_thickness', '0.8')
						put('print_speed', '85')
						put('retraction_hop', '0.1')
						put('bottom_layer_speed', '30')
						put('infill_speed', '110')
						put('inset0_speed', '70')
						put('insetx_speed', '80')
						put('fan_full_height', '5')
						put('fan_speed', '25')
						put('fan_speed_max', '30')
						put('brim_line_count', '8')
					if self.printTypeNormal.GetValue():
						put('layer_height', '0.21')
						put('wall_thickness', '1.05')
						put('solid_layer_thickness', '0.63')
						put('print_speed', '110')
						put('bottom_layer_speed', '25')
						put('inset0_speed', '60')
						put('insetx_speed', '90')
						put('fan_speed', '25')
						put('fan_speed_max', '25')
						put('fill_overlap', '5')
					if self.printTypeHigh.GetValue():
						put('layer_height', '0.14')
						put('solid_layer_thickness', '0.8')
						put('fill_density', '30')
						put('print_speed', '60')
						put('retraction_hop', '0.1')
						put('bottom_layer_speed', '25')
						put('infill_speed', '60')
						put('inset0_speed', '40')
						put('insetx_speed', '50')
						put('fan_full_height', '5')
						put('fan_speed', '40')
						put('fan_speed_max', '75')
						put('skirt_line_count', '4')
			elif self.printMaterialPLA.GetValue():
				if self.printTypeLow.GetValue():
					put('layer_height', '0.28')
					put('wall_thickness', '1.05')
					put('solid_layer_thickness', '0.84')
					put('print_speed', '140')
					put('retraction_speed', '25')
					put('retraction_amount', '3')
					put('retraction_hop', '0.1')
					put('layer0_width_factor', '125')
					put('travel_speed', '180')
					put('bottom_layer_speed', '40')
					put('inset0_speed', '60')
					put('insetx_speed', '100')
					put('cool_min_layer_time', '15')
					put('skirt_minimal_length', '250')
					put('fan_full_height', '1')
					put('fan_speed', '75')
					put('cool_min_feedrate', '15')
					put('brim_line_count', '2')
					put('skirt_line_count', '3')
					put('fill_overlap', '0')
				if self.printTypeNormal.GetValue():
					put('layer_height', '0.21')
					put('solid_layer_thickness', '1')
					put('fill_density', '30')
					put('print_speed', '30')
					put('retraction_speed', '25')
					put('retraction_amount', '3')
					put('retraction_hop', '0.1')
					put('layer0_width_factor', '125')
					put('bottom_layer_speed', '30')
					put('infill_speed', '95')
					put('inset0_speed', '65')
					put('insetx_speed', '75')
					put('cool_min_layer_time', '15')
					put('skirt_minimal_length', '250')
					put('fan_full_height', '1')
					put('fan_speed', '75')
					put('cool_min_feedrate', '15')
					put('brim_line_count', '2')
					put('skirt_line_count', '3')
				if self.printTypeHigh.GetValue():
					put('layer_height', '0.14')
					put('wall_thickness', '1.05')
					put('solid_layer_thickness', '0.56')
					put('fill_density', '30')
					put('print_speed', '100')
					put('retraction_speed', '30')
					put('retraction_amount', '2')
					put('bottom_thickness', '0.25')
					put('layer0_width_factor', '200')
					put('travel_speed', '170')
					put('infill_speed', '75')
					put('inset0_speed', '25')
					put('insetx_speed', '50')
					put('cool_min_layer_time', '20')
					put('skirt_minimal_length', '0')
					put('fan_full_height', '0.28')
					put('brim_line_count', '3')
					put('skirt_line_count', '2')
					put('fill_overlap', '10')
		elif not profile.getMachineSetting('machine_type') == 'lulzbot_mini' and not profile.getMachineSetting('machine_type') == 'lulzbot_TAZ':
			nozzle_size = float(get('nozzle_size'))
			if self.printTypeNormal.GetValue():
				put('layer_height', '0.2')
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

			put('filament_diameter', self.printMaterialDiameter.GetValue())
			if self.printMaterialPLA.GetValue():
				pass
			if self.printMaterialABS.GetValue():
				put('print_bed_temperature', '100')
				put('platform_adhesion', 'Brim')
				put('filament_flow', '107')
				put('print_temperature', '245')
			put('plugin_config', '')

	def updateProfileToControls(self):
		pass
