__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import ConfigParser as configparser
import os.path

from Cura.util import profile
from Cura.util import resources
from Cura.util.simpleModeSettings import SimpleModeSettings

class simpleModePanel(wx.Panel):
	"Main user interface window for Quickprint mode"
	def __init__(self, parent, callback):
		super(simpleModePanel, self).__init__(parent)
		self._callback = callback

		self._print_profile_options = []
		self._print_material_options = []
		self._print_other_options = []

		# This is a hack around an issue where the machine type in the wizard
		# changed and causes some people to have it set to lulzbot_TAZ and some
		# people have it set to lulzbot_TAZ_4.
		# To avoid duplicating the custom settings overrides, we just change the
		# machine_type instead.
		if profile.getMachineSetting('machine_type') == 'lulzbot_TAZ':
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_4')

		printTypePanel = wx.Panel(self)
		for filename in resources.getSimpleModeProfiles():
			cp = configparser.ConfigParser()
			cp.read(filename)
			base_filename = os.path.splitext(os.path.basename(filename))[0]
			name = base_filename
			if cp.has_option('info', 'name'):
				name = cp.get('info', 'name')
			button = wx.RadioButton(printTypePanel, -1, name, style=wx.RB_GROUP if len(self._print_profile_options) == 0 else 0)
			button.base_filename = base_filename
			button.filename = filename
			self._print_profile_options.append(button)
			if profile.getPreference('simpleModeProfile') == base_filename:
				button.SetValue(True)

		printMaterialPanel = wx.Panel(self)
		for filename in resources.getSimpleModeMaterials():
			cp = configparser.ConfigParser()
			cp.read(filename)
			base_filename = os.path.splitext(os.path.basename(filename))[0]
			name = base_filename
			if cp.has_option('info', 'name'):
				name = cp.get('info', 'name')
			button = wx.RadioButton(printMaterialPanel, -1, name, style=wx.RB_GROUP if len(self._print_material_options) == 0 else 0)
			button.base_filename = base_filename
			button.filename = filename
			self._print_material_options.append(button)
			if profile.getPreference('simpleModeMaterial') == base_filename:
				button.SetValue(True)

		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			printMaterialPanel.Show(False)

		for filename in resources.getSimpleModeOptions():
			cp = configparser.ConfigParser()
			cp.read(filename)
			base_filename = os.path.splitext(os.path.basename(filename))[0]
			name = base_filename
			if cp.has_option('info', 'name'):
				name = cp.get('info', 'name')
			button = wx.CheckBox(self, -1, name)
			button.base_filename = base_filename
			button.filename = filename
			self._print_other_options.append(button)

		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)

		sb = wx.StaticBox(printTypePanel, label=_("Select a quickprint profile:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		for button in self._print_profile_options:
			boxsizer.Add(button)
		printTypePanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		printTypePanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(printTypePanel, (0,0), flag=wx.EXPAND)

		sb = wx.StaticBox(printMaterialPanel, label=_("Material:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		for button in self._print_material_options:
			boxsizer.Add(button)
		printMaterialPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		printMaterialPanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(printMaterialPanel, (1,0), flag=wx.EXPAND)

		sb = wx.StaticBox(self, label=_("Other:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		for button in self._print_other_options:
			boxsizer.Add(button)
		sizer.Add(boxsizer, (2,0), flag=wx.EXPAND)

		for button in self._print_profile_options:
			button.Bind(wx.EVT_RADIOBUTTON, self._update)
		for button in self._print_material_options:
			button.Bind(wx.EVT_RADIOBUTTON, self._update)
		for button in self._print_other_options:
			button.Bind(wx.EVT_CHECKBOX, self._update)

	def _update(self, e):
		for button in self._print_profile_options:
			if button.GetValue():
				profile.putPreference('simpleModeProfile', button.base_filename)
		for button in self._print_material_options:
			if button.GetValue():
				profile.putPreference('simpleModeMaterial', button.base_filename)
		self._callback()

	def getSettingOverrides(self):
		settings = {}
		for setting in profile.settingsList:
			if not setting.isProfile():
				continue
			settings[setting.getName()] = setting.getDefault()

		profile_setting = None
		for button in self._print_profile_options:
			if button.GetValue():
				profile_setting = button.base_filename
				break
		material_setting = None
		for button in self._print_material_options:
			if button.GetValue():
				material_setting = button.base_filename
				break
		other_settings = []
		for button in self._print_other_options:
			if button.GetValue():
				other_settings.append(button.base_filename)

		simple_settings = SimpleModeSettings.getSimpleSettings(profile_setting, material_setting, other_settings)
		for setting in simple_settings.keys():
			settings[setting] = simple_settings[setting]

		for button in self._print_profile_options:
			if button.GetValue():
				cp = configparser.ConfigParser()
				cp.read(button.filename)
				for setting in profile.settingsList:
					if setting.isProfile():
						if cp.has_option('profile', setting.getName()):
							settings[setting.getName()] = cp.get('profile', setting.getName())
		if profile.getMachineSetting('gcode_flavor') != 'UltiGCode':
			for button in self._print_material_options:
				if button.GetValue():
					cp = configparser.ConfigParser()
					cp.read(button.filename)
					for setting in profile.settingsList:
						if setting.isProfile():
							if cp.has_option('profile', setting.getName()):
								settings[setting.getName()] = cp.get('profile', setting.getName())

		for button in self._print_other_options:
			if button.GetValue():
				cp = configparser.ConfigParser()
				cp.read(button.filename)
				for setting in profile.settingsList:
					if setting.isProfile():
						if cp.has_option('profile', setting.getName()):
							settings[setting.getName()] = cp.get('profile', setting.getName())

		return settings

	def updateProfileToControls(self):
		pass
