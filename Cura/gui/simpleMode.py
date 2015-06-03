__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import ConfigParser as configparser
import os.path

from Cura.util import profile
from Cura.util import resources

class simpleModePanel(wx.Panel):
	"Main user interface window for Quickprint mode"
	def __init__(self, parent, callback):
		super(simpleModePanel, self).__init__(parent)
		self._callback = callback

		self._print_material_options = []
		self._print_profile_options = []
		self._print_other_options = []

		materials = resources.getSimpleModeMaterials()

		# Create material buttons
		self.printMaterialPanel = wx.Panel(self)
		selectedMaterial = None
		for material in materials:
			if material.disabled:
				continue
			button = wx.RadioButton(self.printMaterialPanel, -1, material.name,
									style=wx.RB_GROUP if len(self._print_material_options) == 0 else 0)
			button.profile = material
			self._print_material_options.append(button)
			if profile.getProfileSetting('simpleModeMaterial') == material.name:
				selectedMaterial = button

		# Decide on the default selected material
		if selectedMaterial is None:
			for button in self._print_material_options:
				if button.profile.default:
					selectedMaterial = button
					break

		if selectedMaterial is None and len(self._print_material_options) > 0:
			selectedMaterial = self._print_material_options[0]

		# Decide to show the panel or not
		if len(self._print_material_options) < 2:
			self.printMaterialPanel.Show(len(self._print_material_options) > 1 and \
										 self._print_material_options[0].profile.always_visible)

		self.printTypePanel = wx.Panel(self)

		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)

		sb = wx.StaticBox(self.printMaterialPanel, label=_("Material:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.SetMinSize((80, 20))
		for button in self._print_material_options:
			boxsizer.Add(button)
		self.printMaterialPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.printMaterialPanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(self.printMaterialPanel, (0,0), border=10, flag=wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP)

		sb = wx.StaticBox(self.printTypePanel, label=_("Select a quickprint profile:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.SetMinSize((180, 20))
		self.printTypePanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.printTypePanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(self.printTypePanel, (1,0), border=10, flag=wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP)


		sb = wx.StaticBox(self, label=_("Other options:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.SetMinSize((100, 20))
		sizer.Add(boxsizer, (2,0), border=10, flag=wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP)
		self.printOptionsSizer = boxsizer

		for button in self._print_material_options:
			button.Bind(wx.EVT_RADIOBUTTON, self._materialSelected)

		if selectedMaterial:
			selectedMaterial.SetValue(True)
			self._materialSelected(None)
		self.Layout()

	def _materialSelected(self, e):
		material = None
		for button in self._print_material_options:
			if button.GetValue():
				material = button.profile

		# Delete profile options
		boxsizer = self.printTypePanel.GetSizer().GetItem(0).GetSizer()
		boxsizer.Clear(True)
		self._print_profile_options = []

		# Add new profiles
		selectedProfile = None
		for print_profile in material.profiles:
			if print_profile.disabled:
				continue
			button = wx.RadioButton(self.printTypePanel, -1, print_profile.name,
									style=wx.RB_GROUP if len(self._print_profile_options) == 0 else 0)
			button.profile = print_profile
			self._print_profile_options.append(button)
			if profile.getProfileSetting('simpleModeProfile') == print_profile.name:
				selectedProfile = button

		# Decide on the profile to be selected by default
		if selectedProfile is None:
			for button in self._print_profile_options:
				if button.profile.default:
					selectedProfile = button
					break

		if selectedProfile is None and len(self._print_profile_options) > 0:
			selectedProfile = self._print_profile_options[0]

		# Decide if we show the profile panel or not
		if len(self._print_profile_options) < 2:
			self.printTypePanel.Show(len(self._print_profile_options) > 0 and \
									 self._print_profile_options[0].profile.always_visible)

		if selectedProfile:
			selectedProfile.SetValue(True)

		# Add profiles to the UI
		for button in self._print_profile_options:
			boxsizer.Add(button)
			button.Bind(wx.EVT_RADIOBUTTON, self._update)

		# Save current selected options
		selected_options = []
		deselected_options = []
		for button in self._print_other_options:
			if button.GetValue():
				selected_options.append(button.profile.name)
			else:
				deselected_options.append(button.profile.name)

		# Delete profile options
		boxsizer = self.printOptionsSizer
		boxsizer.Clear(True)
		self._print_other_options = []

		# Create new options
		for option in material.options:
			if option.disabled:
				continue
			button = wx.CheckBox(self, -1, option.name)
			button.profile = option
			self._print_other_options.append(button)
			# Restore selection on similarly named options
			if option.name in selected_options or \
			   ((not option.name in deselected_options) and option.default):
				button.SetValue(True)

		# Decide if we show the profile panel or not
		# The always_visible doesn't make sense for options since they are checkboxes, and not radio buttons
		if len(self._print_other_options) < 1:
			self.printOptionsPanel.Show(False)

		# Add profiles to the UI
		for button in self._print_other_options:
			boxsizer.Add(button)
			button.Bind(wx.EVT_CHECKBOX, self._update)
		self.Layout()

		# Do not call the callback on the initial UI build
		if e is not None:
			self._update(e)

	def _update(self, e):
		for button in self._print_material_options:
			if button.GetValue():
				profile.putProfileSetting('simpleModeMaterial', button.profile.name)
		for button in self._print_profile_options:
			if button.GetValue():
				profile.putProfileSetting('simpleModeProfile', button.profile.name)
		self._callback()

	def getSettingOverrides(self):
		settings = {}
		for setting in profile.settingsList:
			if setting.isProfile() or setting.isAlteration():
				settings[setting.getName()] = setting.getDefault()

		# Apply materials, profile, then options
		for button in self._print_material_options:
			if button.GetValue():
				settings.update(button.profile.getProfileDict())
		for button in self._print_profile_options:
			if button.GetValue():
				settings.update(button.profile.getProfileDict())
		for button in self._print_other_options:
			if button.GetValue():
				settings.update(button.profile.getProfileDict())

		return settings

	def updateProfileToControls(self):
		pass
