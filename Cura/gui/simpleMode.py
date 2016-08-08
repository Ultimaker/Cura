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
		self._print_material_types = {}
		self._all_print_materials = []

		materials = resources.getSimpleModeMaterials()
		other_print_material_types = []
		for material in materials:
			if material.disabled:
				continue
			if len(material.types) == 0:
				other_print_material_types.append(material)
			else:
				for type in material.types:
					if self._print_material_types.has_key(type):
						self._print_material_types[type].append(material)
					else:
						self._print_material_types[type] = [material]

		if len(self._print_material_types) == 0:
			self._print_material_types = None

		# Create material buttons
		self.printMaterialPanel = wx.Panel(self)
		selectedMaterial = None
		for material in materials:
			if material.disabled:
				continue
			# Show radio buttons if there are no material types
			if self._print_material_types is None:
				button = wx.RadioButton(self.printMaterialPanel, -1, material.name.replace('&', '&&'),
										style=wx.RB_GROUP if len(self._print_material_options) == 0 else 0)
				button.profile = material
				button.Bind(wx.EVT_RADIOBUTTON, self._materialSelected)
				self._print_material_options.append(button)
			self._all_print_materials.append(material)
			if profile.getProfileSetting('simpleModeMaterial') == material.name:
				selectedMaterial = material

		# Decide on the default selected material
		if selectedMaterial is None:
			for material in self._all_print_materials:
				if material.default:
					selectedMaterial = material
					break

		if selectedMaterial is None and len(self._all_print_materials) > 0:
			selectedMaterial = self._all_print_materials[0]

		# Decide to show the panel or not
		if self._print_material_types is None and len(self._print_material_options) < 2:
			self.printMaterialPanel.Show(len(self._print_material_options) > 1 and \
										 self._print_material_options[0].always_visible)

		# Create material types combobox
		self.printMaterialTypesPanel = wx.Panel(self)
		selectedMaterialType = None
		if self._print_material_types is not None:
			for material_type in self._print_material_types:
				if profile.getProfileSetting('simpleModeMaterialType') == material_type and \
				   selectedMaterial in self._print_material_types[material_type]:
					selectedMaterialType = material_type

			if selectedMaterialType is None:
				if profile.getProfileSetting('simpleModeMaterialType') == _("All"):
					selectedMaterialType = profile.getProfileSetting('simpleModeMaterialType')
				elif selectedMaterial is None or len(selectedMaterial.types) == 0:
					selectedMaterialType = _("Others")
				else:
					selectedMaterialType = selectedMaterial.types[0]

		# Decide to show the material types or not
		if self._print_material_types is None:
			self.printMaterialTypesPanel.Show(False)

		self.printTypePanel = wx.Panel(self)

		sizer = wx.GridBagSizer()
		self.SetSizer(sizer)

		boxsizer = wx.BoxSizer(wx.VERTICAL)
		boxsizer.SetMinSize((80, 20))
		if self._print_material_types is None:
			self.materialTypeCombo = None
		else:
			choices = self._print_material_types.keys()
			choices.sort(key=lambda type: sum([mat.order for mat in self._print_material_types[type]]))
			# Now we can add Others, so it appears towards the end
			if len(other_print_material_types) > 0:
				self._print_material_types[_("Others")] = other_print_material_types
				choices.append(_("Others"))
			choices.append(_("All"))
			label = wx.StaticText(self.printMaterialTypesPanel, label=_("Material ease of use:"))
			self.materialTypeCombo = wx.ComboBox(self.printMaterialTypesPanel, -1, selectedMaterialType,
												 choices=choices, style=wx.CB_READONLY)
			self.materialTypeCombo.Bind(wx.EVT_COMBOBOX, self._materialTypeSelected)
			boxsizer.Add(label, flag=wx.EXPAND)
			boxsizer.Add(self.materialTypeCombo, border=5, flag=wx.BOTTOM|wx.TOP|wx.EXPAND)
		self.printMaterialTypesPanel.SetSizer(boxsizer)
		sizer.Add(self.printMaterialTypesPanel, (0,0), border=10, flag=wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP)

		if self._print_material_types is None:
			sb = wx.StaticBox(self.printMaterialPanel, label=_("Material:"))
			boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
			boxsizer.SetMinSize((80, 20))
			for button in self._print_material_options:
				# wxpython 2.8 gives a 13 pixel high radio/checkbutton but wxpython 3.0
				# gives it a 25 pixels height, so we add a border to compensate for the ugliness
				if button.GetBestSize()[1] < 20:
					border = 5
				else:
					border = 0
				boxsizer.Add(button, border=border, flag=wx.ALL)
			self.printMaterialPanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
			self.printMaterialPanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
			self.materialCombo = None
		else: #There are some material types
			boxsizer = wx.BoxSizer(wx.VERTICAL)
			boxsizer.SetMinSize((80, 20))
			label = wx.StaticText(self.printMaterialPanel, label=_("Material:"))
			self.materialCombo = wx.ComboBox(self.printMaterialPanel, -1, selectedMaterial.name,
											 choices=[], style=wx.CB_READONLY)
			self.materialCombo.Bind(wx.EVT_COMBOBOX, self._materialSelected)
			boxsizer.Add(label, flag=wx.EXPAND)
			boxsizer.Add(self.materialCombo, border=5, flag=wx.BOTTOM|wx.TOP|wx.EXPAND)
			self.printMaterialPanel.SetSizer(boxsizer)
		self.materialHyperlink = wx.HyperlinkCtrl(self.printMaterialPanel, -1, label=_('Material Information'), url='',
												  style=wx.HL_ALIGN_LEFT|wx.BORDER_NONE|wx.HL_CONTEXTMENU)
		self.materialHyperlink.Show(False)
		self.materialDescription = wx.StaticText(self.printMaterialPanel, -1, '')
		self.materialDescription.Show(False)
		boxsizer.Add(self.materialDescription, border=5, flag=wx.BOTTOM|wx.TOP|wx.EXPAND)
		boxsizer.Add(self.materialHyperlink, border=5, flag=wx.BOTTOM|wx.TOP|wx.EXPAND)
		sizer.Add(self.printMaterialPanel, (1,0), border=10, flag=wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP)

		sb = wx.StaticBox(self.printTypePanel, label=_("Select a quickprint profile:"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
		boxsizer.SetMinSize((180, 20))
		self.printTypePanel.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.printTypePanel.GetSizer().Add(boxsizer, flag=wx.EXPAND)
		sizer.Add(self.printTypePanel, (2,0), border=10, flag=wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP)


		self.printOptionsBox = wx.StaticBox(self, label=_("Other options:"))
		boxsizer = wx.StaticBoxSizer(self.printOptionsBox, wx.VERTICAL)
		boxsizer.SetMinSize((100, 20))
		sizer.Add(boxsizer, (3,0), border=10, flag=wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP)
		self.printOptionsSizer = boxsizer

		if selectedMaterialType:
			self.materialTypeCombo.SetValue(selectedMaterialType)
			self._materialTypeSelected(None)
		if selectedMaterial:
			if self.materialCombo:
				self.materialCombo.SetValue(selectedMaterial.name)
			else:
				for button in self._print_material_options:
					if button.profile == selectedMaterial:
						button.SetValue(True)
						break
		self._materialSelected(None)
		self.Layout()

	def _materialTypeSelected(self, e):
		materialType = self.materialTypeCombo.GetValue()
		selection = self.materialTypeCombo.GetSelection()
		choices = []

		if selection >= len(self._print_material_types.keys()) or \
		   selection == -1:
			materials = self._all_print_materials
			for material in materials:
				if not material.name.startswith("*"):
					choices.append(material.full_name)
		else:
			materials = self._print_material_types[materialType]
			for material in materials:
				choices.append(material.name)

		# Decide on the default selected material
		selectedMaterial = None
		for material in materials:
			if material.default:
				selectedMaterial = material
				break

		if selectedMaterial is None and len(materials) > 0:
			selectedMaterial = materials[0]

		self.materialCombo.Clear()
		self.materialCombo.AppendItems(choices)
		if len(materials) == 0:
			self.printMaterialTypesPanel.Show(False)
		else:
			self.printMaterialTypesPanel.Show(True)
			self.materialCombo.SetValue(selectedMaterial.name)

		self.materialCombo.Layout()
		self.printMaterialPanel.Layout()
		self._materialSelected(e)

	def _getSelectedMaterial(self):
		if self.materialCombo:
			materialType = self.materialTypeCombo.GetValue()
			selection = self.materialTypeCombo.GetSelection()

			if selection >= len(self._print_material_types.keys()) or \
			   selection == -1:
				materials = self._all_print_materials
			else:
				materials = self._print_material_types[materialType]

			selection = self.materialCombo.GetSelection()

			return materials[selection]
		else:
			for button in self._print_material_options:
				if button.GetValue():
					return button.profile
			return None

	def _materialSelected(self, e):
		material = self._getSelectedMaterial()

		# Delete profile options
		boxsizer = self.printTypePanel.GetSizer().GetItem(0).GetSizer()
		boxsizer.Clear(True)
		self._print_profile_options = []

		if material is None:
			self.printOptionsBox.Show(False)
			self.printTypePanel.Show(False)
			return
		self.printOptionsBox.Show(True)
		self.printTypePanel.Show(True)

		self.materialHyperlink.Show(material.url is not None)
		if material.url:
			self.materialHyperlink.SetURL(material.url)
		self.materialDescription.Show(material.description is not None)
		if material.description:
			self.materialDescription.SetLabel(material.description)

		# Add new profiles
		selectedProfile = None
		for print_profile in material.profiles:
			if print_profile.disabled:
				continue
			button = wx.RadioButton(self.printTypePanel, -1, print_profile.name.replace('&', '&&'),
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
			# wxpython 2.8 gives a 13 pixel high radio/checkbutton but wxpython 3.0
			# gives it a 25 pixels height, so we add a border to compensate for the ugliness
			if button.GetBestSize()[1] < 20:
				border = 5
			else:
				border = 0
			boxsizer.Add(button, border=border, flag=wx.ALL)
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
			button = wx.CheckBox(self, -1, option.name.replace('&', '&&'))
			button.profile = option
			self._print_other_options.append(button)
			# Restore selection on similarly named options
			if option.name in selected_options or \
			   ((not option.name in deselected_options) and option.default):
				button.SetValue(True)

		# Decide if we show the profile panel or not
		# The always_visible doesn't make sense for options since they are checkboxes, and not radio buttons
		self.printOptionsBox.Show(len(self._print_other_options) > 0)

		# Add profiles to the UI
		for button in self._print_other_options:
			# wxpython 2.8 gives a 13 pixel high radio/checkbutton but wxpython 3.0
			# gives it a 25 pixels height, so we add a border to compensate for the ugliness
			if button.GetBestSize()[1] < 20:
				border = 5
			else:
				border = 0
			boxsizer.Add(button, border=border, flag=wx.ALL)
			button.Bind(wx.EVT_CHECKBOX, self._update)

		self.printTypePanel.Layout()
		self.Layout()
		self.GetParent().Fit()

		# Do not call the callback on the initial UI build
		if e is not None:
			self._update(e)

	def _update(self, e):
		if self.materialTypeCombo:
			materialType = self.materialTypeCombo.GetValue()
			profile.putProfileSetting('simpleModeMaterialType', materialType)
		material = self._getSelectedMaterial()
		if material:
			profile.putProfileSetting('simpleModeMaterial', material.name)
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
		material = self._getSelectedMaterial()
		if material:
			settings.update(material.getProfileDict())
		for button in self._print_profile_options:
			if button.GetValue():
				settings.update(button.profile.getProfileDict())
		for button in self._print_other_options:
			if button.GetValue():
				settings.update(button.profile.getProfileDict())

		return settings

	def updateProfileToControls(self):
		pass
