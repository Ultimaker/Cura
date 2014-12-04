__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
from Cura.gui import firmwareInstall
from Cura.util import version
from Cura.util import profile

class newVersionDialog(wx.Dialog):
	def __init__(self):
		super(newVersionDialog, self).__init__(None, title="Welcome to the new version!")

		wx.EVT_CLOSE(self, self.OnClose)

		p = wx.Panel(self)
		self.panel = p
		s = wx.BoxSizer()
		self.SetSizer(s)
		s.Add(p, flag=wx.ALL, border=15)
		s = wx.BoxSizer(wx.VERTICAL)
		p.SetSizer(s)

		title = wx.StaticText(p, -1, 'Cura - ' + version.getVersion())
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		s.Add(title, flag=wx.ALIGN_CENTRE|wx.EXPAND|wx.BOTTOM, border=5)
		s.Add(wx.StaticText(p, -1, 'Welcome to the new version of Cura.'))
		s.Add(wx.StaticText(p, -1, '(This dialog is only shown once)'))
		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=10)
		s.Add(wx.StaticText(p, -1, 'New in this version:'))
		s.Add(wx.StaticText(p, -1, '* Fixed a problem which was introduced in 14.09.\n    There are extreme amounts of head movements generated.'))
		s.Add(wx.StaticText(p, -1, '* Speed up GCode generation for large models by as much as 40%'))
		s.Add(wx.StaticText(p, -1, '* Fixed problems with placement of multiple objects on the build platform'))
		s.Add(wx.StaticText(p, -1, '* Prevent installing firmware for Ultimaker Original+ on an Ultimaker Original'))
		s.Add(wx.StaticText(p, -1, '* Fixed generating big GCode files (more then 200MB) on Windows'))
		s.Add(wx.StaticText(p, -1, '* French translation updates (Thanks to Jeremie Francois)'))
		s.Add(wx.StaticText(p, -1, '* Fixed a problem where "everywhere" support did not work when german was used as language.'))
		s.Add(wx.StaticText(p, -1, '* Changed the handling of the heated bed, now always heats\n    the bed first instead of bed and nozzle at the same time.\n    This to prevent the nozzle from leaking empty.'))
		s.Add(wx.StaticText(p, -1, '* Fixed the "uninstall old Cura versions" option in the windows installer.'))
		s.Add(wx.StaticText(p, -1, '* Improved the search for old installations, so old settings are copied over.'))
		s.Add(wx.StaticText(p, -1, '* Fixed a bug where double clicking a file on windows did not load the file in Cura.'))
		s.Add(wx.StaticText(p, -1, '* Made sure the firmware versions for Ultimaker printers always match the Cura release number.'))
		s.Add(wx.StaticText(p, -1, '* Added a quick access button for expert settings of a certain setting.'))
		s.Add(wx.StaticText(p, -1, '* Added some more raft settings to dial in the raft better.'))
		s.Add(wx.StaticText(p, -1, '* Fixed the tooltip of support material. Now it actually explains the angles properly.'))
		s.Add(wx.StaticText(p, -1, '* Fixed a bug which caused the USB printing window to stop working (Thanks to SpaxGuy)'))
		s.Add(wx.StaticText(p, -1, '* Fix a bug where Cura would stop generating GCode'))
		s.Add(wx.StaticText(p, -1, '* Added latest offerings of Printrbot'))

		self.hasUltimaker = None
		self.hasUltimaker2 = None
		for n in xrange(0, profile.getMachineCount()):
			if profile.getMachineSetting('machine_type', n) == 'ultimaker':
				self.hasUltimaker = n
			if profile.getMachineSetting('machine_type', n) == 'ultimaker2':
				self.hasUltimaker2 = n
		if self.hasUltimaker is not None and False:
			s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=10)
			s.Add(wx.StaticText(p, -1, 'New firmware for your Ultimaker Original:'))
			s.Add(wx.StaticText(p, -1, '* .'))
			button = wx.Button(p, -1, 'Install now')
			self.Bind(wx.EVT_BUTTON, self.OnUltimakerFirmware, button)
			s.Add(button, flag=wx.TOP, border=5)
		if self.hasUltimaker2 is not None:
			s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=10)
			s.Add(wx.StaticText(p, -1, 'New firmware for your Ultimaker2:'))
			s.Add(wx.StaticText(p, -1, '* Detect when the endstops are not working properly.\n    Which prevents the bed from damaging the nozzle.'))
			s.Add(wx.StaticText(p, -1, '* Added the ability to import/export material profiles to the SD card.'))
			s.Add(wx.StaticText(p, -1, '* Improved hotend temperature stability.'))
			s.Add(wx.StaticText(p, -1, '* Added UPET material profile.'))
			s.Add(wx.StaticText(p, -1, '* Minor improvements to the time estimate code.'))
			button = wx.Button(p, -1, 'Install now')
			self.Bind(wx.EVT_BUTTON, self.OnUltimaker2Firmware, button)
			s.Add(button, flag=wx.TOP, border=5)

		s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=10)
		button = wx.Button(p, -1, 'Ok')
		self.Bind(wx.EVT_BUTTON, self.OnOk, button)
		s.Add(button, flag=wx.TOP|wx.ALIGN_RIGHT, border=5)

		self.Fit()
		self.Centre()

	def OnUltimakerFirmware(self, e):
		firmwareInstall.InstallFirmware(machineIndex=self.hasUltimaker)

	def OnUltimaker2Firmware(self, e):
		firmwareInstall.InstallFirmware(machineIndex=self.hasUltimaker2)

	def OnOk(self, e):
		self.Close()

	def OnClose(self, e):
		self.Destroy()
