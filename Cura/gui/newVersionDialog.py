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
		s.Add(wx.StaticText(p, -1, '* Added an expert parameter for the wipe tower size, and made brim go around the wipe tower'))
		s.Add(wx.StaticText(p, -1, '* Added experimental support for printing with the Doodle3D WiFi box'))
		s.Add(wx.StaticText(p, -1, '* Updated object boundaries for multi-object prints, allows for tighter fitting of objects on the build platform'))
		s.Add(wx.StaticText(p, -1, '* Updated time-estimate to greatly improve accuracy of the estimate.'))
		s.Add(wx.StaticText(p, -1, '* Fixed problem with retractions not happening when they should.'))
		s.Add(wx.StaticText(p, -1, '* Added keyboard control for the 3D window to look around with cursor keys.'))

		self.hasUltimaker = None
		self.hasUltimaker2 = None
		for n in xrange(0, profile.getMachineCount()):
			if profile.getMachineSetting('machine_type', n) == 'ultimaker':
				self.hasUltimaker = n
			if profile.getMachineSetting('machine_type', n) == 'ultimaker2':
				self.hasUltimaker2 = n
		if self.hasUltimaker is not None:
			s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=10)
			s.Add(wx.StaticText(p, -1, 'New firmware for your Ultimaker Original:'))
			s.Add(wx.StaticText(p, -1, '* Fixed bug in acceleration planning causing slow moves on rare occasions.'))
			s.Add(wx.StaticText(p, -1, '* Updated to new ErikZalm Marlin base, fixing the long standing slower retraction bug.'))
			button = wx.Button(p, -1, 'Install now')
			self.Bind(wx.EVT_BUTTON, self.OnUltimakerFirmware, button)
			s.Add(button, flag=wx.TOP, border=5)
		if self.hasUltimaker2 is not None:
			s.Add(wx.StaticLine(p), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=10)
			s.Add(wx.StaticText(p, -1, 'New firmware for your Ultimaker2:'))
			s.Add(wx.StaticText(p, -1, '* Fixed bug in acceleration planning causing slow moves on rare occasions.'))
			s.Add(wx.StaticText(p, -1, '* Fixed the problem where aborting a print did not always home the head.'))
			s.Add(wx.StaticText(p, -1, '* Disabled normal LCD menu curing USB printing.'))
			s.Add(wx.StaticText(p, -1, '* Disable stepper drivers after print is finished or aborted, so you can manually move the head.'))
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
