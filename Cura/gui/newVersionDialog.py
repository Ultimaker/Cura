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
		s.Add(wx.StaticText(p, -1, '* Improved the LayerView rendering speed.'))
		s.Add(wx.StaticText(p, -1, '* Made the LayerView update during slicing, so you can see the result before it is ready.'))
		s.Add(wx.StaticText(p, -1, '* New USB printing dialog, smaller, cleaner.'))
		s.Add(wx.StaticText(p, -1, '* Selectable USB printing dialogs, from plugins.'))
		s.Add(wx.StaticText(p, -1, '* Selection between new grid or old line based support material.'))
		s.Add(wx.StaticText(p, -1, '* Profile settings are now stored per machine instead of global for all machines.'))
		s.Add(wx.StaticText(p, -1, '* Added TweakAtZ 3.1 plugin per default. Thanks to Steve Morlock, Ricardo Gomez and Stefan Heule.'))
		s.Add(wx.StaticText(p, -1, '* Added separate speeds for outer and inner shells.'))
		s.Add(wx.StaticText(p, -1, '* Added expert Z-Hop feature.'))
		s.Add(wx.StaticText(p, -1, '* Removed need for temp files, which speeds up Cura on slower harddisks.'))
		s.Add(wx.StaticText(p, -1, '* Added expert setting to configure support material angle.'))
		s.Add(wx.StaticText(p, -1, '* Allow round printer beds for Deltabots.'))

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
			s.Add(wx.StaticText(p, -1, '* Added pause function during printing.'))
			s.Add(wx.StaticText(p, -1, '* Added material selection when changing material.'))
			s.Add(wx.StaticText(p, -1, '* Fixed the move material maintenance function.'))
			s.Add(wx.StaticText(p, -1, '* Fixed the led brightness on startup.'))
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
