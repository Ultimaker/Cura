__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import os
import webbrowser
import sys


from Cura.gui import configBase
from Cura.gui import expertConfig
from Cura.gui import alterationPanel
from Cura.gui import pluginPanel
from Cura.gui import preferencesDialog
from Cura.gui import configWizard
from Cura.gui import firmwareInstall
from Cura.gui import simpleMode
from Cura.gui import sceneView
from Cura.gui import aboutWindow
from Cura.gui.util import dropTarget
#from Cura.gui.tools import batchRun
from Cura.gui.tools import pidDebugger
from Cura.gui.tools import minecraftImport
from Cura.util import profile
from Cura.util import version
import platform
from Cura.util import meshLoader

class mainWindow(wx.Frame):
	def __init__(self):
		super(mainWindow, self).__init__(None, title='Cura - ' + version.getVersion())

		wx.EVT_CLOSE(self, self.OnClose)

		# allow dropping any file, restrict later
		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles))

		# TODO: wxWidgets 2.9.4 has a bug when NSView does not register for dragged types when wx drop target is set. It was fixed in 2.9.5
		if sys.platform.startswith('darwin'):
			try:
				import objc
				nswindow = objc.objc_object(c_void_p=self.MacGetTopLevelWindowRef())
				view = nswindow.contentView()
				view.registerForDraggedTypes_([u'NSFilenamesPboardType'])
			except:
				pass

		self.normalModeOnlyItems = []

		mruFile = os.path.join(profile.getBasePath(), 'mru_filelist.ini')
		self.config = wx.FileConfig(appName="Cura",
						localFilename=mruFile,
						style=wx.CONFIG_USE_LOCAL_FILE)

		self.ID_MRU_MODEL1, self.ID_MRU_MODEL2, self.ID_MRU_MODEL3, self.ID_MRU_MODEL4, self.ID_MRU_MODEL5, self.ID_MRU_MODEL6, self.ID_MRU_MODEL7, self.ID_MRU_MODEL8, self.ID_MRU_MODEL9, self.ID_MRU_MODEL10 = [wx.NewId() for line in xrange(10)]
		self.modelFileHistory = wx.FileHistory(10, self.ID_MRU_MODEL1)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Load(self.config)

		self.ID_MRU_PROFILE1, self.ID_MRU_PROFILE2, self.ID_MRU_PROFILE3, self.ID_MRU_PROFILE4, self.ID_MRU_PROFILE5, self.ID_MRU_PROFILE6, self.ID_MRU_PROFILE7, self.ID_MRU_PROFILE8, self.ID_MRU_PROFILE9, self.ID_MRU_PROFILE10 = [wx.NewId() for line in xrange(10)]
		self.profileFileHistory = wx.FileHistory(10, self.ID_MRU_PROFILE1)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Load(self.config)

		self.menubar = wx.MenuBar()
		self.fileMenu = wx.Menu()
		i = self.fileMenu.Append(-1, _("Load model file...\tCTRL+L"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showLoadModel(), i)
		i = self.fileMenu.Append(-1, _("Save model...\tCTRL+S"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveModel(), i)
		i = self.fileMenu.Append(-1, _("Reload platform\tF5"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.reloadScene(e), i)
		i = self.fileMenu.Append(-1, _("Clear platform"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.OnDeleteAll(e), i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Print...\tCTRL+P"))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.OnPrintButton(1), i)
		i = self.fileMenu.Append(-1, _("Save GCode..."))
		self.Bind(wx.EVT_MENU, lambda e: self.scene.showSaveGCode(), i)
		i = self.fileMenu.Append(-1, _("Show slice engine log..."))
		self.Bind(wx.EVT_MENU, lambda e: self.scene._showEngineLog(), i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Open Profile..."))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfile, i)
		i = self.fileMenu.Append(-1, _("Save Profile..."))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnSaveProfile, i)
		i = self.fileMenu.Append(-1, _("Load Profile from GCode..."))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnLoadProfileFromGcode, i)
		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Reset Profile to default"))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnResetProfile, i)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(-1, _("Preferences...\tCTRL+,"))
		self.Bind(wx.EVT_MENU, self.OnPreferences, i)
		i = self.fileMenu.Append(-1, _("Machine settings..."))
		self.Bind(wx.EVT_MENU, self.OnMachineSettings, i)
		self.fileMenu.AppendSeparator()

		# Model MRU list
		modelHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), '&' + _("Recent Model Files"), modelHistoryMenu)
		self.modelFileHistory.UseMenu(modelHistoryMenu)
		self.modelFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnModelMRU, id=self.ID_MRU_MODEL1, id2=self.ID_MRU_MODEL10)

		# Profle MRU list
		profileHistoryMenu = wx.Menu()
		self.fileMenu.AppendMenu(wx.NewId(), _("Recent Profile Files"), profileHistoryMenu)
		self.profileFileHistory.UseMenu(profileHistoryMenu)
		self.profileFileHistory.AddFilesToMenu()
		self.Bind(wx.EVT_MENU_RANGE, self.OnProfileMRU, id=self.ID_MRU_PROFILE1, id2=self.ID_MRU_PROFILE10)

		self.fileMenu.AppendSeparator()
		i = self.fileMenu.Append(wx.ID_EXIT, _("Quit"))
		self.Bind(wx.EVT_MENU, self.OnQuit, i)
		self.menubar.Append(self.fileMenu, '&' + _("File"))

		toolsMenu = wx.Menu()
		#i = toolsMenu.Append(-1, 'Batch run...')
		#self.Bind(wx.EVT_MENU, self.OnBatchRun, i)
		#self.normalModeOnlyItems.append(i)

		if minecraftImport.hasMinecraft():
			i = toolsMenu.Append(-1, _("Minecraft map import..."))
			self.Bind(wx.EVT_MENU, self.OnMinecraftImport, i)

		if version.isDevVersion():
			i = toolsMenu.Append(-1, _("PID Debugger..."))
			self.Bind(wx.EVT_MENU, self.OnPIDDebugger, i)

		i = toolsMenu.Append(-1, _("Copy profile to clipboard"))
		self.Bind(wx.EVT_MENU, self.onCopyProfileClipboard,i)

		toolsMenu.AppendSeparator()
		self.allAtOnceItem = toolsMenu.Append(-1, _("Print all at once"), kind=wx.ITEM_RADIO)
		self.Bind(wx.EVT_MENU, self.onOneAtATimeSwitch, self.allAtOnceItem)
		self.oneAtATime = toolsMenu.Append(-1, _("Print one at a time"), kind=wx.ITEM_RADIO)
		self.Bind(wx.EVT_MENU, self.onOneAtATimeSwitch, self.oneAtATime)
		if profile.getPreference('oneAtATime') == 'True':
			self.oneAtATime.Check(True)
		else:
			self.allAtOnceItem.Check(True)

		self.menubar.Append(toolsMenu, _("Tools"))

		#Machine menu for machine configuration/tooling
		self.machineMenu = wx.Menu()
		self.updateMachineMenu()

		self.menubar.Append(self.machineMenu, _("Machine"))

		expertMenu = wx.Menu()
		i = expertMenu.Append(-1, _("Switch to quickprint..."), kind=wx.ITEM_RADIO)
		self.switchToQuickprintMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnSimpleSwitch, i)

		i = expertMenu.Append(-1, _("Switch to full settings..."), kind=wx.ITEM_RADIO)
		self.switchToNormalMenuItem = i
		self.Bind(wx.EVT_MENU, self.OnNormalSwitch, i)
		expertMenu.AppendSeparator()

		i = expertMenu.Append(-1, _("Open expert settings...\tCTRL+E"))
		self.normalModeOnlyItems.append(i)
		self.Bind(wx.EVT_MENU, self.OnExpertOpen, i)
		expertMenu.AppendSeparator()
		i = expertMenu.Append(-1, _("Run first run wizard..."))
		self.Bind(wx.EVT_MENU, self.OnFirstRunWizard, i)
		self.bedLevelWizardMenuItem = expertMenu.Append(-1, _("Run bed leveling wizard..."))
		self.Bind(wx.EVT_MENU, self.OnBedLevelWizard, self.bedLevelWizardMenuItem)
		self.headOffsetWizardMenuItem = expertMenu.Append(-1, _("Run head offset wizard..."))
		self.Bind(wx.EVT_MENU, self.OnHeadOffsetWizard, self.headOffsetWizardMenuItem)

		self.menubar.Append(expertMenu, _("Expert"))

		helpMenu = wx.Menu()
		i = helpMenu.Append(-1, _("Online documentation..."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('http://daid.github.com/Cura'), i)
		i = helpMenu.Append(-1, _("Report a problem..."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://github.com/daid/Cura/issues'), i)
		i = helpMenu.Append(-1, _("Check for update..."))
		self.Bind(wx.EVT_MENU, self.OnCheckForUpdate, i)
		i = helpMenu.Append(-1, _("Open YouMagine website..."))
		self.Bind(wx.EVT_MENU, lambda e: webbrowser.open('https://www.youmagine.com/'), i)
		i = helpMenu.Append(-1, _("About Cura..."))
		self.Bind(wx.EVT_MENU, self.OnAbout, i)
		self.menubar.Append(helpMenu, _("Help"))
		self.SetMenuBar(self.menubar)

		self.splitter = wx.SplitterWindow(self, style = wx.SP_3D | wx.SP_LIVE_UPDATE)
		self.leftPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.rightPane = wx.Panel(self.splitter, style=wx.BORDER_NONE)
		self.splitter.Bind(wx.EVT_SPLITTER_DCLICK, lambda evt: evt.Veto())

		##Gui components##
		self.simpleSettingsPanel = simpleMode.simpleModePanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.normalSettingsPanel = normalSettingsPanel(self.leftPane, lambda : self.scene.sceneUpdated())

		self.leftSizer = wx.BoxSizer(wx.VERTICAL)
		self.leftSizer.Add(self.simpleSettingsPanel, 1)
		self.leftSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.leftPane.SetSizer(self.leftSizer)

		#Preview window
		self.scene = sceneView.SceneView(self.rightPane)

		#Main sizer, to position the preview window, buttons and tab control
		sizer = wx.BoxSizer()
		self.rightPane.SetSizer(sizer)
		sizer.Add(self.scene, 1, flag=wx.EXPAND)

		# Main window sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		sizer.Add(self.splitter, 1, wx.EXPAND)
		sizer.Layout()
		self.sizer = sizer

		self.updateProfileToAllControls()

		self.SetBackgroundColour(self.normalSettingsPanel.GetBackgroundColour())

		self.simpleSettingsPanel.Show(False)
		self.normalSettingsPanel.Show(False)

		# Set default window size & position
		self.SetSize((wx.Display().GetClientArea().GetWidth()/2,wx.Display().GetClientArea().GetHeight()/2))
		self.Centre()

		#Timer set; used to check if profile is on the clipboard
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer)
		self.timer.Start(1000)
		self.lastTriedClipboard = profile.getProfileString()

		# Restore the window position, size & state from the preferences file
		try:
			if profile.getPreference('window_maximized') == 'True':
				self.Maximize(True)
			else:
				posx = int(profile.getPreference('window_pos_x'))
				posy = int(profile.getPreference('window_pos_y'))
				width = int(profile.getPreference('window_width'))
				height = int(profile.getPreference('window_height'))
				if posx > 0 or posy > 0:
					self.SetPosition((posx,posy))
				if width > 0 and height > 0:
					self.SetSize((width,height))

			self.normalSashPos = int(profile.getPreference('window_normal_sash'))
		except:
			self.normalSashPos = 0
			self.Maximize(True)
		if self.normalSashPos < self.normalSettingsPanel.printPanel.GetBestSize()[0] + 5:
			self.normalSashPos = self.normalSettingsPanel.printPanel.GetBestSize()[0] + 5

		self.splitter.SplitVertically(self.leftPane, self.rightPane, self.normalSashPos)

		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.Centre()
		if wx.Display.GetFromPoint((self.GetPositionTuple()[0] + self.GetSizeTuple()[1], self.GetPositionTuple()[1] + self.GetSizeTuple()[1])) < 0:
			self.Centre()
		if wx.Display.GetFromPoint(self.GetPosition()) < 0:
			self.SetSize((800,600))
			self.Centre()

		self.updateSliceMode()
		self.scene.SetFocus()

	def onTimer(self, e):
		#Check if there is something in the clipboard
		profileString = ""
		try:
			if not wx.TheClipboard.IsOpened():
				if not wx.TheClipboard.Open():
					return
				do = wx.TextDataObject()
				if wx.TheClipboard.GetData(do):
					profileString = do.GetText()
				wx.TheClipboard.Close()

				startTag = "CURA_PROFILE_STRING:"
				if startTag in profileString:
					#print "Found correct syntax on clipboard"
					profileString = profileString.replace("\n","").strip()
					profileString = profileString[profileString.find(startTag)+len(startTag):]
					if profileString != self.lastTriedClipboard:
						print profileString
						self.lastTriedClipboard = profileString
						profile.setProfileFromString(profileString)
						self.scene.notification.message("Loaded new profile from clipboard.")
						self.updateProfileToAllControls()
		except:
			print "Unable to read from clipboard"


	def updateSliceMode(self):
		isSimple = profile.getPreference('startMode') == 'Simple'

		self.normalSettingsPanel.Show(not isSimple)
		self.simpleSettingsPanel.Show(isSimple)
		self.leftPane.Layout()

		for i in self.normalModeOnlyItems:
			i.Enable(not isSimple)
		if isSimple:
			self.switchToQuickprintMenuItem.Check()
		else:
			self.switchToNormalMenuItem.Check()

		# Set splitter sash position & size
		if isSimple:
			# Save normal mode sash
			self.normalSashPos = self.splitter.GetSashPosition()

			# Change location of sash to width of quick mode pane
			(width, height) = self.simpleSettingsPanel.GetSizer().GetSize()
			self.splitter.SetSashPosition(width, True)

			# Disable sash
			self.splitter.SetSashSize(0)
		else:
			self.splitter.SetSashPosition(self.normalSashPos, True)
			# Enabled sash
			self.splitter.SetSashSize(4)
		self.defaultFirmwareInstallMenuItem.Enable(firmwareInstall.getDefaultFirmware() is not None)
		if profile.getMachineSetting('machine_type') == 'ultimaker2':
			self.bedLevelWizardMenuItem.Enable(False)
			self.headOffsetWizardMenuItem.Enable(False)
		if int(profile.getMachineSetting('extruder_amount')) < 2:
			self.headOffsetWizardMenuItem.Enable(False)
		self.scene.updateProfileToControls()
		self.scene._scene.pushFree()

	def onOneAtATimeSwitch(self, e):
		profile.putPreference('oneAtATime', self.oneAtATime.IsChecked())
		if self.oneAtATime.IsChecked() and profile.getMachineSettingFloat('extruder_head_size_height') < 1:
			wx.MessageBox(_('For "One at a time" printing, you need to have entered the correct head size and gantry height in the machine settings'), _('One at a time warning'), wx.OK | wx.ICON_WARNING)
		self.scene.updateProfileToControls()
		self.scene._scene.pushFree()
		self.scene.sceneUpdated()

	def OnPreferences(self, e):
		prefDialog = preferencesDialog.preferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()
		wx.CallAfter(prefDialog.Show)

	def OnMachineSettings(self, e):
		prefDialog = preferencesDialog.machineSettingsDialog(self)
		prefDialog.Centre()
		prefDialog.Show()
		prefDialog.Raise()

	def OnDropFiles(self, files):
		if len(files) > 0:
			self.updateProfileToAllControls()
		self.scene.loadFiles(files)

	def OnModelMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_MODEL1
		path = self.modelFileHistory.GetHistoryFile(fileNum)
		# Update Model MRU
		self.modelFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()
		# Load Model
		profile.putPreference('lastFile', path)
		filelist = [ path ]
		self.scene.loadFiles(filelist)

	def addToModelMRU(self, file):
		self.modelFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ModelMRU")
		self.modelFileHistory.Save(self.config)
		self.config.Flush()

	def OnProfileMRU(self, e):
		fileNum = e.GetId() - self.ID_MRU_PROFILE1
		path = self.profileFileHistory.GetHistoryFile(fileNum)
		# Update Profile MRU
		self.profileFileHistory.AddFileToHistory(path)  # move up the list
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()
		# Load Profile
		profile.loadProfile(path)
		self.updateProfileToAllControls()

	def addToProfileMRU(self, file):
		self.profileFileHistory.AddFileToHistory(file)
		self.config.SetPath("/ProfileMRU")
		self.profileFileHistory.Save(self.config)
		self.config.Flush()

	def updateProfileToAllControls(self):
		self.scene.updateProfileToControls()
		self.normalSettingsPanel.updateProfileToControls()
		self.simpleSettingsPanel.updateProfileToControls()

	def reloadSettingPanels(self):
		self.leftSizer.Detach(self.simpleSettingsPanel)
		self.leftSizer.Detach(self.normalSettingsPanel)
		self.simpleSettingsPanel.Destroy()
		self.normalSettingsPanel.Destroy()
		self.simpleSettingsPanel = simpleMode.simpleModePanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.normalSettingsPanel = normalSettingsPanel(self.leftPane, lambda : self.scene.sceneUpdated())
		self.leftSizer.Add(self.simpleSettingsPanel, 1)
		self.leftSizer.Add(self.normalSettingsPanel, 1, wx.EXPAND)
		self.updateSliceMode()
		self.updateProfileToAllControls()

	def updateMachineMenu(self):
		#Remove all items so we can rebuild the menu. Inserting items seems to cause crashes, so this is the safest way.
		for item in self.machineMenu.GetMenuItems():
			self.machineMenu.RemoveItem(item)

		#Add a menu item for each machine configuration.
		for n in xrange(0, profile.getMachineCount()):
			i = self.machineMenu.Append(n + 0x1000, profile.getMachineSetting('machine_name', n).title(), kind=wx.ITEM_RADIO)
			if n == int(profile.getPreferenceFloat('active_machine')):
				i.Check(True)
			self.Bind(wx.EVT_MENU, lambda e: self.OnSelectMachine(e.GetId() - 0x1000), i)

		self.machineMenu.AppendSeparator()

		i = self.machineMenu.Append(-1, _("Machine settings..."))
		self.Bind(wx.EVT_MENU, self.OnMachineSettings, i)

		#Add tools for machines.
		self.machineMenu.AppendSeparator()

		self.defaultFirmwareInstallMenuItem = self.machineMenu.Append(-1, _("Install default firmware..."))
		self.Bind(wx.EVT_MENU, self.OnDefaultMarlinFirmware, self.defaultFirmwareInstallMenuItem)

		i = self.machineMenu.Append(-1, _("Install custom firmware..."))
		self.Bind(wx.EVT_MENU, self.OnCustomFirmware, i)

	def OnLoadProfile(self, e):
		dlg=wx.FileDialog(self, _("Select profile file to load"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			profile.loadProfile(profileFile)
			self.updateProfileToAllControls()

			# Update the Profile MRU
			self.addToProfileMRU(profileFile)
		dlg.Destroy()

	def OnLoadProfileFromGcode(self, e):
		dlg=wx.FileDialog(self, _("Select gcode file to load profile from"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("gcode files (*%s)|*%s;*%s" % (profile.getGCodeExtension(), profile.getGCodeExtension(), profile.getGCodeExtension()[0:2]))
		if dlg.ShowModal() == wx.ID_OK:
			gcodeFile = dlg.GetPath()
			f = open(gcodeFile, 'r')
			hasProfile = False
			for line in f:
				if line.startswith(';CURA_PROFILE_STRING:'):
					profile.setProfileFromString(line[line.find(':')+1:].strip())
					if ';{profile_string}' not in profile.getAlterationFile('end.gcode'):
						profile.setAlterationFile('end.gcode', profile.getAlterationFile('end.gcode') + '\n;{profile_string}')
					hasProfile = True
			if hasProfile:
				self.updateProfileToAllControls()
			else:
				wx.MessageBox(_("No profile found in GCode file.\nThis feature only works with GCode files made by Cura 12.07 or newer."), _("Profile load error"), wx.OK | wx.ICON_INFORMATION)
		dlg.Destroy()

	def OnSaveProfile(self, e):
		dlg=wx.FileDialog(self, _("Select profile file to save"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("ini files (*.ini)|*.ini")
		if dlg.ShowModal() == wx.ID_OK:
			profileFile = dlg.GetPath()
			if not profileFile.lower().endswith('.ini'): #hack for linux, as for some reason the .ini is not appended.
				profileFile += '.ini'
			profile.saveProfile(profileFile)
		dlg.Destroy()

	def OnResetProfile(self, e):
		dlg = wx.MessageDialog(self, _("This will reset all profile settings to defaults.\nUnless you have saved your current profile, all settings will be lost!\nDo you really want to reset?"), _("Profile reset"), wx.YES_NO | wx.ICON_QUESTION)
		result = dlg.ShowModal() == wx.ID_YES
		dlg.Destroy()
		if result:
			profile.resetProfile()
			self.updateProfileToAllControls()

	def OnSimpleSwitch(self, e):
		profile.putPreference('startMode', 'Simple')
		self.updateSliceMode()

	def OnNormalSwitch(self, e):
		profile.putPreference('startMode', 'Normal')
		self.updateSliceMode()

	def OnDefaultMarlinFirmware(self, e):
		firmwareInstall.InstallFirmware()

	def OnCustomFirmware(self, e):
		if profile.getMachineSetting('machine_type').startswith('ultimaker'):
			wx.MessageBox(_("Warning: Installing a custom firmware does not guarantee that you machine will function correctly, and could damage your machine."), _("Firmware update"), wx.OK | wx.ICON_EXCLAMATION)
		dlg=wx.FileDialog(self, _("Open firmware to upload"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("HEX file (*.hex)|*.hex;*.HEX")
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			dlg.Destroy()
			if not(os.path.exists(filename)):
				return
			#For some reason my Ubuntu 10.10 crashes here.
			firmwareInstall.InstallFirmware(filename)

	def OnFirstRunWizard(self, e):
		self.Hide()
		configWizard.configWizard()
		self.Show()
		self.reloadSettingPanels()

	def OnSelectMachine(self, index):
		profile.setActiveMachine(index)
		self.reloadSettingPanels()

	def OnBedLevelWizard(self, e):
		configWizard.bedLevelWizard()

	def OnHeadOffsetWizard(self, e):
		configWizard.headOffsetWizard()

	def OnExpertOpen(self, e):
		ecw = expertConfig.expertConfigWindow(lambda : self.scene.sceneUpdated())
		ecw.Centre()
		ecw.Show()

	def OnMinecraftImport(self, e):
		mi = minecraftImport.minecraftImportWindow(self)
		mi.Centre()
		mi.Show(True)

	def OnPIDDebugger(self, e):
		debugger = pidDebugger.debuggerWindow(self)
		debugger.Centre()
		debugger.Show(True)

	def onCopyProfileClipboard(self, e):
		try:
			if not wx.TheClipboard.IsOpened():
				wx.TheClipboard.Open()
				clipData = wx.TextDataObject()
				self.lastTriedClipboard = profile.getProfileString()
				profileString = profile.insertNewlines("CURA_PROFILE_STRING:" + self.lastTriedClipboard)
				clipData.SetText(profileString)
				wx.TheClipboard.SetData(clipData)
				wx.TheClipboard.Close()
		except:
			print "Could not write to clipboard, unable to get ownership. Another program is using the clipboard."

	def OnCheckForUpdate(self, e):
		newVersion = version.checkForNewerVersion()
		if newVersion is not None:
			if wx.MessageBox(_("A new version of Cura is available, would you like to download?"), _("New version available"), wx.YES_NO | wx.ICON_INFORMATION) == wx.YES:
				webbrowser.open(newVersion)
		else:
			wx.MessageBox(_("You are running the latest version of Cura!"), _("Awesome!"), wx.ICON_INFORMATION)

	def OnAbout(self, e):
		aboutBox = aboutWindow.aboutWindow()
		aboutBox.Centre()
		aboutBox.Show()

	def OnClose(self, e):
		profile.saveProfile(profile.getDefaultProfilePath(), True)

		# Save the window position, size & state from the preferences file
		profile.putPreference('window_maximized', self.IsMaximized())
		if not self.IsMaximized() and not self.IsIconized():
			(posx, posy) = self.GetPosition()
			profile.putPreference('window_pos_x', posx)
			profile.putPreference('window_pos_y', posy)
			(width, height) = self.GetSize()
			profile.putPreference('window_width', width)
			profile.putPreference('window_height', height)

			# Save normal sash position.  If in normal mode (!simple mode), get last position of sash before saving it...
			isSimple = profile.getPreference('startMode') == 'Simple'
			if not isSimple:
				self.normalSashPos = self.splitter.GetSashPosition()
			profile.putPreference('window_normal_sash', self.normalSashPos)

		#HACK: Set the paint function of the glCanvas to nothing so it won't keep refreshing. Which can keep wxWidgets from quiting.
		print "Closing down"
		self.scene.OnPaint = lambda e : e
		self.scene._engine.cleanup()
		self.Destroy()

	def OnQuit(self, e):
		self.Close()

class normalSettingsPanel(configBase.configPanelBase):
	"Main user interface window"
	def __init__(self, parent, callback = None):
		super(normalSettingsPanel, self).__init__(parent, callback)

		#Main tabs
		self.nb = wx.Notebook(self)
		self.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
		self.GetSizer().Add(self.nb, 1, wx.EXPAND)

		(left, right, self.printPanel) = self.CreateDynamicConfigTab(self.nb, 'Basic')
		self._addSettingsToPanels('basic', left, right)
		self.SizeLabelWidths(left, right)

		(left, right, self.advancedPanel) = self.CreateDynamicConfigTab(self.nb, 'Advanced')
		self._addSettingsToPanels('advanced', left, right)
		self.SizeLabelWidths(left, right)

		#Plugin page
		self.pluginPanel = pluginPanel.pluginPanel(self.nb, callback)
		self.nb.AddPage(self.pluginPanel, _("Plugins"))

		#Alteration page
		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			self.alterationPanel = None
		else:
			self.alterationPanel = alterationPanel.alterationPanel(self.nb, callback)
			self.nb.AddPage(self.alterationPanel, "Start/End-GCode")

		self.Bind(wx.EVT_SIZE, self.OnSize)

		self.nb.SetSize(self.GetSize())
		self.UpdateSize(self.printPanel)
		self.UpdateSize(self.advancedPanel)

	def _addSettingsToPanels(self, category, left, right):
		count = len(profile.getSubCategoriesFor(category)) + len(profile.getSettingsForCategory(category))

		p = left
		n = 0
		for title in profile.getSubCategoriesFor(category):
			n += 1 + len(profile.getSettingsForCategory(category, title))
			if n > count / 2:
				p = right
			configBase.TitleRow(p, _(title))
			for s in profile.getSettingsForCategory(category, title):
				configBase.SettingRow(p, s.getName())

	def SizeLabelWidths(self, left, right):
		leftWidth = self.getLabelColumnWidth(left)
		rightWidth = self.getLabelColumnWidth(right)
		maxWidth = max(leftWidth, rightWidth)
		self.setLabelColumnWidth(left, maxWidth)
		self.setLabelColumnWidth(right, maxWidth)

	def OnSize(self, e):
		# Make the size of the Notebook control the same size as this control
		self.nb.SetSize(self.GetSize())

		# Propegate the OnSize() event (just in case)
		e.Skip()

		# Perform out resize magic
		self.UpdateSize(self.printPanel)
		self.UpdateSize(self.advancedPanel)

	def UpdateSize(self, configPanel):
		sizer = configPanel.GetSizer()

		# Pseudocde
		# if horizontal:
		#     if width(col1) < best_width(col1) || width(col2) < best_width(col2):
		#         switch to vertical
		# else:
		#     if width(col1) > (best_width(col1) + best_width(col1)):
		#         switch to horizontal
		#

		col1 = configPanel.leftPanel
		colSize1 = col1.GetSize()
		colBestSize1 = col1.GetBestSize()
		col2 = configPanel.rightPanel
		colSize2 = col2.GetSize()
		colBestSize2 = col2.GetBestSize()

		orientation = sizer.GetOrientation()

		if orientation == wx.HORIZONTAL:
			if (colSize1[0] <= colBestSize1[0]) or (colSize2[0] <= colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.VERTICAL)
				sizer.Add(configPanel.leftPanel, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()
		else:
			if max(colSize1[0], colSize2[0]) > (colBestSize1[0] + colBestSize2[0]):
				configPanel.Freeze()
				sizer = wx.BoxSizer(wx.HORIZONTAL)
				sizer.Add(configPanel.leftPanel, proportion=1, border=35, flag=wx.EXPAND)
				sizer.Add(configPanel.rightPanel, proportion=1, flag=wx.EXPAND)
				configPanel.SetSizer(sizer)
				#sizer.Layout()
				configPanel.Layout()
				self.Layout()
				configPanel.Thaw()

	def updateProfileToControls(self):
		super(normalSettingsPanel, self).updateProfileToControls()
		if self.alterationPanel is not None:
			self.alterationPanel.updateProfileToControls()
		self.pluginPanel.updateProfileToControls()
