from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.gui import configWizard
from Cura.gui import configBase
from Cura.util import machineCom
from Cura.util import profile

class preferencesDialog(wx.Dialog):
	def __init__(self, parent):
		super(preferencesDialog, self).__init__(None, title="Preferences")

		wx.EVT_CLOSE(self, self.OnClose)

		self.parent = parent
		extruderCount = int(profile.getMachineSetting('extruder_amount'))

		self.panel = configBase.configPanelBase(self)

		left, right, main = self.panel.CreateConfigPanel(self)

		configBase.TitleRow(left, _("Colours"))
		configBase.SettingRow(left, 'model_colour', wx.Colour)
		for i in xrange(1, extruderCount):
			configBase.SettingRow(left, 'model_colour%d' % (i+1), wx.Colour)

		configBase.TitleRow(right, _("Filament settings"))
		configBase.SettingRow(right, 'filament_physical_density')
		configBase.SettingRow(right, 'filament_cost_kg')
		configBase.SettingRow(right, 'filament_cost_meter')

		#configBase.TitleRow(right, 'Slicer settings')
		#configBase.SettingRow(right, 'save_profile')

		#configBase.TitleRow(right, 'SD Card settings')

		configBase.TitleRow(right, _("Cura settings"))
		configBase.SettingRow(right, 'auto_detect_sd')
		configBase.SettingRow(right, 'check_for_updates')
		configBase.SettingRow(right, 'submit_slice_information')

		self.okButton = wx.Button(right, -1, 'Ok')
		right.GetSizer().Add(self.okButton, (right.GetSizer().GetRows(), 0), flag=wx.BOTTOM, border=5)
		self.okButton.Bind(wx.EVT_BUTTON, lambda e: self.Close())

		main.Fit()
		self.Fit()

	def OnClose(self, e):
		#self.parent.reloadSettingPanels()
		self.Destroy()

class machineSettingsDialog(wx.Dialog):
	def __init__(self, parent):
		super(machineSettingsDialog, self).__init__(None, title="Machine settings")

		wx.EVT_CLOSE(self, self.OnClose)

		self.parent = parent
		extruderCount = int(profile.getMachineSetting('extruder_amount'))

		self.panel = configBase.configPanelBase(self)
		self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.GetSizer().Add(self.panel, 1, wx.EXPAND)
		self.nb = wx.Notebook(self.panel)
		self.panel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.panel.GetSizer().Add(self.nb, 1, wx.EXPAND)

		for idx in xrange(0, profile.getMachineCount()):
			left, right, main = self.panel.CreateConfigPanel(self.nb)
			configBase.TitleRow(left, _("Machine settings"))
			configBase.SettingRow(left, 'steps_per_e', index=idx)
			configBase.SettingRow(left, 'machine_width', index=idx)
			configBase.SettingRow(left, 'machine_depth', index=idx)
			configBase.SettingRow(left, 'machine_height', index=idx)
			configBase.SettingRow(left, 'extruder_amount', index=idx)
			configBase.SettingRow(left, 'has_heated_bed', index=idx)
			configBase.SettingRow(left, 'gcode_flavor', index=idx)

			configBase.TitleRow(right, _("Printer head size"))
			configBase.SettingRow(right, 'extruder_head_size_min_x', index=idx)
			configBase.SettingRow(right, 'extruder_head_size_min_y', index=idx)
			configBase.SettingRow(right, 'extruder_head_size_max_x', index=idx)
			configBase.SettingRow(right, 'extruder_head_size_max_y', index=idx)
			configBase.SettingRow(right, 'extruder_head_size_height', index=idx)

			for i in xrange(1, extruderCount):
				configBase.TitleRow(left, _("Extruder %d") % (i+1))
				configBase.SettingRow(left, 'extruder_offset_x%d' % (i), index=idx)
				configBase.SettingRow(left, 'extruder_offset_y%d' % (i), index=idx)

			configBase.TitleRow(right, _("Communication settings"))
			configBase.SettingRow(right, 'serial_port', ['AUTO'] + machineCom.serialList(), index=idx)
			configBase.SettingRow(right, 'serial_baud', ['AUTO'] + map(str, machineCom.baudrateList()), index=idx)

			self.nb.AddPage(main, profile.getMachineSetting('machine_name', idx).title())

		self.nb.SetSelection(int(profile.getPreferenceFloat('active_machine')))

		self.buttonPanel = wx.Panel(self.panel)
		self.panel.GetSizer().Add(self.buttonPanel)

		self.buttonPanel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.okButton = wx.Button(self.buttonPanel, -1, 'Ok')
		self.okButton.Bind(wx.EVT_BUTTON, lambda e: self.Close())
		self.buttonPanel.GetSizer().Add(self.okButton, flag=wx.ALL, border=5)

		self.addButton = wx.Button(self.buttonPanel, -1, 'Add new machine')
		self.addButton.Bind(wx.EVT_BUTTON, self.OnAddMachine)
		self.buttonPanel.GetSizer().Add(self.addButton, flag=wx.ALL, border=5)

		self.remButton = wx.Button(self.buttonPanel, -1, 'Remove machine')
		self.remButton.Bind(wx.EVT_BUTTON, self.OnRemoveMachine)
		self.buttonPanel.GetSizer().Add(self.remButton, flag=wx.ALL, border=5)

		main.Fit()
		self.Fit()

	def OnAddMachine(self, e):
		self.Hide()
		self.parent.Hide()
		profile.setActiveMachine(profile.getMachineCount())
		configWizard.configWizard(True)
		self.parent.Show()
		self.parent.reloadSettingPanels()
		self.parent.updateMachineMenu()

		prefDialog = machineSettingsDialog(self.parent)
		prefDialog.Centre()
		prefDialog.Show()
		wx.CallAfter(self.Close)

	def OnRemoveMachine(self, e):
		if profile.getMachineCount() < 2:
			wx.MessageBox(_("Cannot remove the last machine configuration in Cura"), _("Machine remove error"), wx.OK | wx.ICON_ERROR)
			return

		self.Hide()
		profile.removeMachine(self.nb.GetSelection())
		self.parent.reloadSettingPanels()
		self.parent.updateMachineMenu()

		prefDialog = machineSettingsDialog(self.parent)
		prefDialog.Centre()
		prefDialog.Show()
		wx.CallAfter(self.Close)

	def OnClose(self, e):
		self.parent.reloadSettingPanels()
		self.Destroy()
