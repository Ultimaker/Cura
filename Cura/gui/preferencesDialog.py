from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.gui import configBase
from Cura.util import removableStorage
from Cura.util import machineCom
from Cura.util import profile

class preferencesDialog(wx.Dialog):
	def __init__(self, parent):
		super(preferencesDialog, self).__init__(None, title="Preferences")
		
		wx.EVT_CLOSE(self, self.OnClose)
		
		self.parent = parent
		self.oldExtruderAmount = int(profile.getPreference('extruder_amount'))

		self.panel = configBase.configPanelBase(self)
		
		left, right, main = self.panel.CreateConfigPanel(self)
		configBase.TitleRow(left, 'Machine settings')
		configBase.SettingRow(left, 'steps_per_e')
		configBase.SettingRow(left, 'machine_width')
		configBase.SettingRow(left, 'machine_depth')
		configBase.SettingRow(left, 'machine_height')
		configBase.SettingRow(left, 'extruder_amount')
		configBase.SettingRow(left, 'has_heated_bed')

		configBase.TitleRow(left, 'Printer head size')
		configBase.SettingRow(left, 'extruder_head_size_min_x')
		configBase.SettingRow(left, 'extruder_head_size_min_y')
		configBase.SettingRow(left, 'extruder_head_size_max_x')
		configBase.SettingRow(left, 'extruder_head_size_max_y')
		configBase.SettingRow(left, 'extruder_head_size_height')

		for i in xrange(1, self.oldExtruderAmount):
			configBase.TitleRow(left, 'Extruder %d' % (i+1))
			configBase.SettingRow(left, 'extruder_offset_x%d' % (i))
			configBase.SettingRow(left, 'extruder_offset_y%d' % (i))

		configBase.TitleRow(right, 'Colours')
		configBase.SettingRow(right, 'model_colour', wx.Colour)
		for i in xrange(1, self.oldExtruderAmount):
			configBase.SettingRow(right, 'model_colour%d' % (i+1), wx.Colour)

		configBase.TitleRow(right, 'Filament settings')
		configBase.SettingRow(right, 'filament_physical_density')
		configBase.SettingRow(right, 'filament_cost_kg')
		configBase.SettingRow(right, 'filament_cost_meter')

		configBase.TitleRow(right, 'Communication settings')
		configBase.SettingRow(right, 'serial_port', ['AUTO'] + machineCom.serialList())
		configBase.SettingRow(right, 'serial_baud', ['AUTO'] + map(str, machineCom.baudrateList()))

		#configBase.TitleRow(right, 'Slicer settings')
		#configBase.SettingRow(right, 'save_profile')

		#configBase.TitleRow(right, 'SD Card settings')

		configBase.TitleRow(right, 'Cura settings')
		configBase.SettingRow(right, 'auto_detect_sd')
		configBase.SettingRow(right, 'check_for_updates')
		configBase.SettingRow(right, 'submit_slice_information')

		self.okButton = wx.Button(right, -1, 'Ok')
		right.GetSizer().Add(self.okButton, (right.GetSizer().GetRows(), 0), flag=wx.BOTTOM, border=5)
		self.okButton.Bind(wx.EVT_BUTTON, lambda e: self.Close())
		
		main.Fit()
		self.Fit()

	def OnClose(self, e):
		if self.oldExtruderAmount != int(profile.getPreference('extruder_amount')):
			wx.MessageBox('After changing the amount of extruders you need to restart Cura for full effect.', 'Extruder amount warning.', wx.OK | wx.ICON_INFORMATION)
		self.parent.updateProfileToControls()
		self.Destroy()
