__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import wx
import threading
import sys
import time

from Cura.avr_isp import stk500v2
from Cura.avr_isp import ispBase
from Cura.avr_isp import intelHex

from Cura.util import machineCom
from Cura.util import profile
from Cura.util import resources

def getDefaultFirmware(machineIndex = None):
	if profile.getMachineSetting('machine_type', machineIndex) == 'ultimaker':
		name = 'MarlinUltimaker'
		if profile.getMachineSettingFloat('extruder_amount', machineIndex) > 2:
			return None
		if profile.getMachineSetting('has_heated_bed', machineIndex) == 'True':
			name += '-HBK'
		if sys.platform.startswith('linux'):
			name += '-115200'
		else:
			name += '-250000'
		if profile.getMachineSettingFloat('extruder_amount', machineIndex) > 1:
			name += '-dual'
		return resources.getPathForFirmware(name + '.hex')

	if profile.getMachineSetting('machine_type', machineIndex) == 'ultimaker2':
		return resources.getPathForFirmware("MarlinUltimaker2.hex")
	if profile.getMachineSetting('machine_type', machineIndex) == 'Witbox':
		return resources.getPathForFirmware("MarlinWitbox.hex")
	return None

class InstallFirmware(wx.Dialog):
	def __init__(self, filename = None, port = None, machineIndex = None):
		super(InstallFirmware, self).__init__(parent=None, title="Firmware install for %s" % (profile.getMachineSetting('machine_name', machineIndex).title()), size=(250, 100))
		if port is None:
			port = profile.getMachineSetting('serial_port')
		if filename is None:
			filename = getDefaultFirmware(machineIndex)
		if filename is None:
			wx.MessageBox(_("I am sorry, but Cura does not ship with a default firmware for your machine configuration."), _("Firmware update"), wx.OK | wx.ICON_ERROR)
			self.Destroy()
			return
		if profile.getMachineSetting('machine_type', machineIndex) == 'reprap':
			wx.MessageBox(_("Cura only supports firmware updates for ATMega2560 based hardware.\nSo updating your RepRap with Cura might or might not work."), _("Firmware update"), wx.OK | wx.ICON_INFORMATION)

		sizer = wx.BoxSizer(wx.VERTICAL)

		self.progressLabel = wx.StaticText(self, -1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\nX')
		sizer.Add(self.progressLabel, 0, flag=wx.ALIGN_CENTER|wx.ALL, border=5)
		self.progressGauge = wx.Gauge(self, -1)
		sizer.Add(self.progressGauge, 0, flag=wx.EXPAND)
		self.okButton = wx.Button(self, -1, _("OK"))
		self.okButton.Disable()
		self.okButton.Bind(wx.EVT_BUTTON, self.OnOk)
		sizer.Add(self.okButton, 0, flag=wx.ALIGN_CENTER|wx.ALL, border=5)
		self.SetSizer(sizer)

		self.filename = filename
		self.port = port

		self.Layout()
		self.Fit()

		self.thread = threading.Thread(target=self.OnRun)
		self.thread.daemon = True
		self.thread.start()

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
			wx.CallAfter(self.updateLabel, _("Please connect the printer to\nyour computer with the USB cable."))
			while not programmer.isConnected():
				for self.port in machineCom.serialList(True):
					try:
						programmer.connect(self.port)
						break
					except ispBase.IspError:
						pass
				time.sleep(1)
				if not self:
					#Window destroyed
					return
		else:
			try:
				programmer.connect(self.port)
			except ispBase.IspError:
				pass

		if not programmer.isConnected():
			wx.MessageBox(_("Failed to find machine for firmware upgrade\nIs your machine connected to the PC?"),
						  _("Firmware update"), wx.OK | wx.ICON_ERROR)
			wx.CallAfter(self.Close)
			return

		wx.CallAfter(self.updateLabel, _("Uploading firmware..."))
		try:
			programmer.programChip(hexFile)
			wx.CallAfter(self.updateLabel, _("Done!\nInstalled firmware: %s") % (os.path.basename(self.filename)))
		except ispBase.IspError as e:
			wx.CallAfter(self.updateLabel, _("Failed to write firmware.\n") + str(e))

		programmer.close()
		wx.CallAfter(self.okButton.Enable)

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

