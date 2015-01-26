__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import wx
import threading
import sys
import time
import serial

from Cura.avr_isp import stk500v2
from Cura.avr_isp import ispBase
from Cura.avr_isp import intelHex

from Cura.gui.util import taskbar
from Cura.util import machineCom
from Cura.util import profile
from Cura.util import resources

def getDefaultFirmware(machineIndex = None):
	machine_type = profile.getMachineSetting('machine_type', machineIndex)
	extruders = profile.getMachineSettingFloat('extruder_amount', machineIndex)
	heated_bed = profile.getMachineSetting('has_heated_bed', machineIndex) == 'True'
	baudrate = 250000
	if sys.platform.startswith('linux'):
		baudrate = 115200
	if machine_type == 'ultimaker':
		name = 'MarlinUltimaker'
		if extruders > 2:
			return None
		if heated_bed:
			name += '-HBK'
		name += '-%d' % (baudrate)
		if extruders > 1:
			name += '-dual'
		return resources.getPathForFirmware(name + '.hex')

	if machine_type == 'ultimaker_plus':
		name = 'MarlinUltimaker-UMOP-%d' % (baudrate)
		if extruders > 2:
			return None
		if extruders > 1:
			name += '-dual'
		return resources.getPathForFirmware(name + '.hex')

	if machine_type == 'ultimaker2':
		if extruders > 2:
			return None
		if extruders > 1:
			return resources.getPathForFirmware("MarlinUltimaker2-dual.hex")
		return resources.getPathForFirmware("MarlinUltimaker2.hex")
	if machine_type == 'ultimaker2go':
		return resources.getPathForFirmware("MarlinUltimaker2go.hex")
	if machine_type == 'ultimaker2extended':
		if extruders > 2:
			return None
		if extruders > 1:
			return resources.getPathForFirmware("MarlinUltimaker2extended-dual.hex")
		return resources.getPathForFirmware("MarlinUltimaker2extended.hex")
	if machine_type == 'Witbox':
		return resources.getPathForFirmware("MarlinWitbox.hex")
	return None

class InstallFirmware(wx.Dialog):
	def __init__(self, parent = None, filename = None, port = None, machineIndex = None):
		super(InstallFirmware, self).__init__(parent=parent, title="Firmware install for %s" % (profile.getMachineSetting('machine_name', machineIndex).title()), size=(250, 100))
		if port is None:
			port = profile.getMachineSetting('serial_port')
		if filename is None:
			filename = getDefaultFirmware(machineIndex)
		if filename is None:
			wx.MessageBox(_("I am sorry, but Cura does not ship with a default firmware for your machine configuration."), _("Firmware update"), wx.OK | wx.ICON_ERROR)
			self.Destroy()
			return
		self._machine_type = profile.getMachineSetting('machine_type', machineIndex)
		if self._machine_type == 'reprap':
			wx.MessageBox(_("Cura only supports firmware updates for ATMega2560 based hardware.\nSo updating your RepRap with Cura might or might not work."), _("Firmware update"), wx.OK | wx.ICON_INFORMATION)

		sizer = wx.BoxSizer(wx.VERTICAL)

		self.progressLabel = wx.StaticText(self, -1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\nX\nX')
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
						programmer.close()
				time.sleep(1)
				if not self:
					#Window destroyed
					return
		else:
			try:
				programmer.connect(self.port)
			except ispBase.IspError:
				programmer.close()

		if not programmer.isConnected():
			wx.MessageBox(_("Failed to find machine for firmware upgrade\nIs your machine connected to the PC?"),
						  _("Firmware update"), wx.OK | wx.ICON_ERROR)
			wx.CallAfter(self.Close)
			return

		if self._machine_type == 'ultimaker':
			if programmer.hasChecksumFunction():
				wx.CallAfter(self.updateLabel, _("Failed to install firmware:\nThis firmware is not compatible with this machine.\nTrying to install UMO firmware on an UM2 or UMO+?"))
				programmer.close()
				wx.CallAfter(self.okButton.Enable)
				return
		if self._machine_type == 'ultimaker_plus' or self._machine_type == 'ultimaker2':
			if not programmer.hasChecksumFunction():
				wx.CallAfter(self.updateLabel, _("Failed to install firmware:\nThis firmware is not compatible with this machine.\nTrying to install UM2 or UMO+ firmware on an UMO?"))
				programmer.close()
				wx.CallAfter(self.okButton.Enable)
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
		taskbar.setProgress(self.GetParent(), value, max)

	def OnOk(self, e):
		self.Close()
		taskbar.setBusy(self.GetParent(), False)

	def OnClose(self, e):
		self.Destroy()


class AutoUpdateFirmware(wx.Dialog):
	def __init__(self, parent, filename = None, port = None, machineIndex = None):
		super(AutoUpdateFirmware, self).__init__(parent=parent, title="Auto Firmware install", size=(250, 500))
		if port is None:
			port = profile.getMachineSetting('serial_port')
		self._serial = None

		sizer = wx.BoxSizer(wx.VERTICAL)

		self.progressLabel = wx.StaticText(self, -1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\nX\nX')
		sizer.Add(self.progressLabel, 0, flag=wx.ALIGN_CENTER|wx.ALL, border=5)
		self.progressGauge = wx.Gauge(self, -1)
		sizer.Add(self.progressGauge, 0, flag=wx.EXPAND)
		self.okButton = wx.Button(self, -1, _("OK"))
		self.okButton.Bind(wx.EVT_BUTTON, self.OnOk)
		sizer.Add(self.okButton, 0, flag=wx.ALIGN_CENTER|wx.ALL, border=5)

		f = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False)
		self._termLog = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_DONTWRAP)
		self._termLog.SetFont(f)
		self._termLog.SetEditable(0)
		self._termLog.SetMinSize((1, 400))
		self._termInput = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self._termInput.SetFont(f)
		sizer.Add(self._termLog, 0, flag=wx.ALIGN_CENTER|wx.ALL|wx.EXPAND)
		sizer.Add(self._termInput, 0, flag=wx.ALIGN_CENTER|wx.ALL|wx.EXPAND)

		self.Bind(wx.EVT_TEXT_ENTER, self.OnTermEnterLine, self._termInput)

		self.SetSizer(sizer)

		self.filename = filename
		self.port = port

		self.Layout()
		self.Fit()

		self.thread = threading.Thread(target=self.OnRun)
		self.thread.daemon = True
		self.thread.start()

		self.read_thread = threading.Thread(target=self.OnSerialRead)
		self.read_thread.daemon = True
		self.read_thread.start()

		self.ShowModal()
		self.Destroy()
		return

	def _addTermLog(self, line):
		if self._termLog is not None:
			if len(self._termLog.GetValue()) > 10000:
				self._termLog.SetValue(self._termLog.GetValue()[-10000:])
			self._termLog.SetInsertionPointEnd()
			if type(line) != unicode:
				line = unicode(line, 'utf-8', 'replace')
			self._termLog.AppendText(line.encode('utf-8', 'replace'))

	def OnTermEnterLine(self, e):
		lines = self._termInput.GetValue().split(';')
		for line in lines:
			if line == '':
				continue
			self._addTermLog('> %s\n' % (line))
			if self._serial is not None:
				self._serial.write(line + '\n')

	def OnRun(self):
		mtime = 0
		while bool(self):
			new_mtime = os.stat(self.filename).st_mtime
			if mtime != new_mtime:
				mtime = new_mtime
				if self._serial is not None:
					self._serial.close()
					self._serial = None
				time.sleep(0.5)
				self.OnInstall()
				try:
					self._serial = serial.Serial(self.port, 115200)
				except:
					pass
			time.sleep(0.5)

	def OnSerialRead(self):
		while bool(self):
			if self._serial is None:
				time.sleep(0.5)
			else:
				try:
					line = self._serial.readline()
					wx.CallAfter(self._addTermLog, line)
				except:
					pass

	def OnInstall(self):
		wx.CallAfter(self.okButton.Disable)
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
			wx.CallAfter(self.updateLabel, _("Failed to connect to programmer.\n"))
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
		taskbar.setProgress(self.GetParent(), value, max)

	def OnOk(self, e):
		self.Close()
		taskbar.setBusy(self.GetParent(), False)

	def OnClose(self, e):
		self.Destroy()

