__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import ConfigParser as configparser
import os.path

from Cura.util import profile
import cPickle as pickle
from Cura.util import resources

class simpleModePanel(wx.Panel):
	"Main user interface window for Quickprint mode"
	def __init__(self, parent, callback):
		super(simpleModePanel, self).__init__(parent)
		self._callback = callback

		self._print_profile_options = []
		self._print_material_options = []

		printTypePanel = wx.Panel(self)
		for filename in resources.getSimpleModeProfiles():
			cp = configparser.ConfigParser()
			cp.read(filename)
			name = os.path.basename(filename)
			if cp.has_option('info', 'name'):
				name = cp.get('info', 'name')
			button = wx.RadioButton(printTypePanel, -1, name, style=wx.RB_GROUP if len(self._print_profile_options) == 0 else 0)
			button.filename = filename
			self._print_profile_options.append(button)

		printMaterialPanel = wx.Panel(self)
		for filename in resources.getSimpleModeMaterials():
			cp = configparser.ConfigParser()
			cp.read(filename)
			name = os.path.basename(filename)
			if cp.has_option('info', 'name'):
				name = cp.get('info', 'name')
			button = wx.RadioButton(printMaterialPanel, -1, name, style=wx.RB_GROUP if len(self._print_material_options) == 0 else 0)
			button.filename = filename
			self._print_material_options.append(button)
		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			printMaterialPanel.Show(False)

		self.printSupport = wx.CheckBox(self, -1, _("Print support structure"))
		self.printBrim = wx.CheckBox(self, -1, _("Print Brim"))

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
		boxsizer.Add(self.printSupport)
		boxsizer.Add(self.printBrim)
		sizer.Add(boxsizer, (2,0), flag=wx.EXPAND)

		for button in self._print_profile_options:
			button.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())
		for button in self._print_material_options:
			button.Bind(wx.EVT_RADIOBUTTON, lambda e: self._callback())

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

	def getSettingOverrides(self):
		settings = {}
		for setting in profile.settingsList:
			if not setting.isProfile():
				continue
			settings[setting.getName()] = setting.getDefault()

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


		if self.printSupport.GetValue():
			settings['support'] = "Exterior Only"
		return settings

	def updateProfileToControls(self):
		pass
