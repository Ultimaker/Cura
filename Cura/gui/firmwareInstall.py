from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os, wx, threading, sys

from Cura.avr_isp import stk500v2
from Cura.avr_isp import ispBase
from Cura.avr_isp import intelHex

from Cura.util import machineCom
from Cura.util import profile
from Cura.util import resources

def getDefaultFirmware():
	if profile.getMachineSetting('machine_type') == 'ultimaker':
		if profile.getMachineSetting('has_heated_bed') == 'True':
			return None
		if profile.getMachineSettingFloat('extruder_amount') > 2:
			return None
		if profile.getMachineSettingFloat('extruder_amount') > 1:
			if sys.platform.startswith('linux'):
				return resources.getPathForFirmware("MarlinUltimaker-115200-dual.hex")
			else:
				return resources.getPathForFirmware("MarlinUltimaker-250000-dual.hex")
		if sys.platform.startswith('linux'):
			return resources.getPathForFirmware("MarlinUltimaker-115200.hex")
		else:
			return resources.getPathForFirmware("MarlinUltimaker-250000.hex")
	return None

class InstallFirmware(wx.Dialog):
	def __init__(self, filename = None, port = None):
		super(InstallFirmware, self).__init__(parent=None, title="Firmware install", size=(250, 100))
		if port is None:
			port = profile.getMachineSetting('serial_port')
		if filename is None:
			filename = getDefaultFirmware()
		if filename is None:
			wx.MessageBox(_("I am sorry, but Cura does not ship with a default firmware for your machine configuration."), _("Firmware update"), wx.OK | wx.ICON_ERROR)
			self.Destroy()
			return

		sizer = wx.BoxSizer(wx.VERTICAL)

		self.progressLabel = wx.StaticText(self, -1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\nX')
		sizer.Add(self.progressLabel, 0, flag=wx.ALIGN_CENTER)
		self.progressGauge = wx.Gauge(self, -1)
		sizer.Add(self.progressGauge, 0, flag=wx.EXPAND)
		self.okButton = wx.Button(self, -1, _("OK"))
		self.okButton.Disable()
		self.okButton.Bind(wx.EVT_BUTTON, self.OnOk)
		sizer.Add(self.okButton, 0, flag=wx.ALIGN_CENTER)
		self.SetSizer(sizer)

		self.filename = filename
		self.port = port

		self.Layout()
		self.Fit()

		threading.Thread(target=self.OnRun).start()

		self.ShowModal()
		self.Destroy()
		return

	def OnRun(self):
		wx.CallAfter(self.updateLabel, _("Reading firmware..."))
		hexFile = intelHex.readHex(self.filename)
		wx.CallAfter(self.updateLabel, _("Connecting to machine..."))
		programmer = stk500v2.Stk500v2()
		programmer.progressCallback = self.OnProgress
		if self.port == 'AUTO':
			for self.port in machineCom.serialList(True):
				try:
					programmer.connect(self.port)
					break
				except ispBase.IspError:
					pass
		else:
			try:
				programmer.connect(self.port)
			except ispBase.IspError:
				pass

		if programmer.isConnected():
			wx.CallAfter(self.updateLabel, _("Uploading firmware..."))
			try:
				programmer.programChip(hexFile)
				wx.CallAfter(self.updateLabel, _("Done!\nInstalled firmware: %s") % (os.path.basename(self.filename)))
			except ispBase.IspError as e:
				wx.CallAfter(self.updateLabel, _("Failed to write firmware.\n") + str(e))

			programmer.close()
			wx.CallAfter(self.okButton.Enable)
			return
		wx.MessageBox(_("Failed to find machine for firmware upgrade\nIs your machine connected to the PC?"),
					  _("Firmware update"), wx.OK | wx.ICON_ERROR)
		wx.CallAfter(self.Close)

	def updateLabel(self, text):
		self.progressLabel.SetLabel(text)
		#self.Layout()

	def OnProgress(self, value, max):
		wx.CallAfter(self.progressGauge.SetRange, max)
		wx.CallAfter(self.progressGauge.SetValue, value)

	def OnOk(self, e):
		self.Close()

	def OnClose(self, e):
		self.Destroy()

