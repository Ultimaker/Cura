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
		s.Add(wx.StaticText(p, -1, '* Added feature to configure the first layer to use wider print lines, for better adhesion to the printer bed.'))
		s.Add(wx.StaticText(p, -1, '* Added all Printrbot printer variations.'))
		s.Add(wx.StaticText(p, -1, 'New in version 14.06.1:'))
		s.Add(wx.StaticText(p, -1, '* Updated drivers for Windows 8.1.'))
		s.Add(wx.StaticText(p, -1, '* Added better raft support with surface layers and an air-gap. Special thanks to Gregoire Passault.'))
		s.Add(wx.StaticText(p, -1, '* Improved outer surface quality on high detail prints.'))
		s.Add(wx.StaticText(p, -1, '* Fixed bug with multiple machines and different start/end GCode.'))
		s.Add(wx.StaticText(p, -1, '* Added initial support for BitsFromBytes machines.'))
		s.Add(wx.StaticText(p, -1, '* Improved the Pronterface UI with buttons to set temperature and extrusion buttons.'))
		s.Add(wx.StaticText(p, -1, '* Improved bridging detection.'))

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
			s.Add(wx.StaticText(p, -1, 'New firmware for your Ultimaker2: (14.07.0)'))
			s.Add(wx.StaticText(p, -1, '* Added feature in the maintenance menu to just load filament'))
			s.Add(wx.StaticText(p, -1, '* Fixed grinding problem at the start of a print'))
			s.Add(wx.StaticText(p, -1, '* Fixed properly retracting when a print is finished'))
			s.Add(wx.StaticText(p, -1, 'Firmware update: (14.06.2)'))
			s.Add(wx.StaticText(p, -1, '* Fixed a problem with the bed leveling. (Special thanks to stevegt for figuring this out)'))
			s.Add(wx.StaticText(p, -1, '* Improved the start of the print, first moves the bed up before moving to the print.'))
			s.Add(wx.StaticText(p, -1, '* Improved the start of the print, initial filament push is slower so it does not slip.'))
			s.Add(wx.StaticText(p, -1, '* Made sure the head does not bump into the front of the casing at first startup.'))
			s.Add(wx.StaticText(p, -1, '* Fixed support for the PauseAtZ plugin.'))
			s.Add(wx.StaticText(p, -1, '* Added lifetime runtime stats. Allows you to see how long the printer has been running.'))
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
