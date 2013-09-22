from __future__ import absolute_import
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
		self.printMaterialDiameter = wx.TextCtrl(printMaterialPanel, -1, profile.getProfileSetting('filament_diameter'))
		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			printMaterialPanel.Show(False)
		
		self.printSupport = wx.CheckBox(self, -1, _("Print support structure"))

		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)

		sb = wx.StaticBox(printTypePanel, label=_("Select a print type:"))
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
		self.printMaterialDiameter.Bind(wx.EVT_TEXT, lambda e: self._callback())

		self.printSupport.Bind(wx.EVT_CHECKBOX, lambda e: self._callback())

	def setupSlice(self):
		put = profile.setTempOverride
		get = profile.getProfileSetting

		put('layer_height', '0.2')
		put('wall_thickness', '0.8')
		put('solid_layer_thickness', '0.6')
		put('fill_density', '20')
		put('skirt_line_count', '1')
		put('skirt_gap', '6.0')
		put('print_speed', '50')
		put('print_temperature', '220')
		put('support', 'None')
		put('retraction_enable', 'True')
		put('retraction_min_travel', '5.0')
		put('retraction_speed', '40.0')
		put('retraction_amount', '4.5')
		put('retraction_extra', '0.0')
		put('travel_speed', '150')
		put('max_z_speed', '3.0')
		put('bottom_layer_speed', '25')
		put('cool_min_layer_time', '5')
		put('fan_enabled', 'True')
		put('fan_layer', '1')
		put('fan_speed', '100')
		put('extra_base_wall_thickness', '0.0')
		put('sequence', 'Loops > Perimeter > Infill')
		put('force_first_layer_sequence', 'True')
		put('infill_type', 'Line')
		put('solid_top', 'True')
		put('fill_overlap', '15')
		put('support_rate', '80')
		put('support_distance', '0.5')
		put('joris', 'False')
		put('cool_min_feedrate', '5')
		put('bridge_speed', '100')
		put('raft_margin', '5')
		put('raft_base_material_amount', '100')
		put('raft_interface_material_amount', '100')
		put('bottom_thickness', '0.3')

		if self.printSupport.GetValue():
			put('support', _("Exterior Only"))

		nozzle_size = float(get('nozzle_size'))
		if self.printTypeNormal.GetValue():
			put('wall_thickness', nozzle_size * 2.0)
			put('layer_height', '0.10')
			put('fill_density', '20')
		elif self.printTypeLow.GetValue():
			put('wall_thickness', nozzle_size * 2.5)
			put('layer_height', '0.20')
			put('fill_density', '10')
			put('print_speed', '50')
			put('cool_min_layer_time', '3')
			put('bottom_layer_speed', '30')
		elif self.printTypeHigh.GetValue():
			put('wall_thickness', nozzle_size * 2.0)
			put('layer_height', '0.06')
			put('fill_density', '20')
			put('bottom_layer_speed', '15')
		elif self.printTypeJoris.GetValue():
			put('wall_thickness', nozzle_size * 1.5)
			put('layer_height', '0.3')
			put('solid_layer_thickness', '0.9')
			put('fill_density', '0')
			put('joris', 'True')
			put('extra_base_wall_thickness', '15.0')
			put('sequence', 'Infill > Loops > Perimeter')
			put('force_first_layer_sequence', 'False')
			put('solid_top', 'False')
			put('support', 'None')
			put('cool_min_layer_time', '3')

		put('filament_diameter', self.printMaterialDiameter.GetValue())
		if self.printMaterialPLA.GetValue():
			put('filament_density', '1.00')
			put('enable_raft', 'False')
			put('skirt_line_count', '1')
		if self.printMaterialABS.GetValue():
			put('filament_density', '0.85')
			put('enable_raft', 'True')
			put('skirt_line_count', '0')
			put('fan_layer', '1')
			put('bottom_thickness', '0.0')
			put('print_temperature', '245')
		put('plugin_config', '')

	def updateProfileToControls(self):
		pass
