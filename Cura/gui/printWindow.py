__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
from wx.lib.intctrl import IntCtrl
try:
	import power
except:
	power = None
import time
import sys
import os
import ctypes
import subprocess
from Cura.util import resources
from Cura.util import profile
from Cura.util import version

TIME_FORMAT = "%H:%M:%S"

#TODO: This does not belong here!
if sys.platform.startswith('win'):
	def preventComputerFromSleeping(frame, prevent):
		"""
		Function used to prevent the computer from going into sleep mode.
		:param prevent: True = Prevent the system from going to sleep from this point on.
		:param prevent: False = No longer prevent the system from going to sleep.
		"""
		ES_CONTINUOUS = 0x80000000
		ES_SYSTEM_REQUIRED = 0x00000001
		ES_AWAYMODE_REQUIRED = 0x00000040
		#SetThreadExecutionState returns 0 when failed, which is ignored. The function should be supported from windows XP and up.
		if prevent:
			# For Vista and up we use ES_AWAYMODE_REQUIRED to prevent a print from failing if the PC does go to sleep
			# As it's not supported on XP, we catch the error and fallback to using ES_SYSTEM_REQUIRED only
			if ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED) == 0:
				ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
		else:
			ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

elif sys.platform.startswith('darwin'):
	import objc
	bundle = objc.initFrameworkWrapper("IOKit",
	frameworkIdentifier="com.apple.iokit",
	frameworkPath=objc.pathForFramework("/System/Library/Frameworks/IOKit.framework"),
	globals=globals())
	foo = objc.loadBundleFunctions(bundle, globals(), [("IOPMAssertionCreateWithName", b"i@I@o^I")])
	foo = objc.loadBundleFunctions(bundle, globals(), [("IOPMAssertionRelease", b"iI")])
	def preventComputerFromSleeping(frame, prevent):
		if prevent:
			success, preventComputerFromSleeping.assertionID = IOPMAssertionCreateWithName(kIOPMAssertionTypeNoDisplaySleep, kIOPMAssertionLevelOn, "Cura is printing", None)
			if success != kIOReturnSuccess:
				preventComputerFromSleeping.assertionID = None
		else:
			if hasattr(preventComputerFromSleeping, "assertionID"):
				if preventComputerFromSleeping.assertionID is not None:
					IOPMAssertionRelease(preventComputerFromSleeping.assertionID)
					preventComputerFromSleeping.assertionID = None
else:
	def preventComputerFromSleeping(frame, prevent):
		if os.path.isfile("/usr/bin/xdg-screensaver"):
			try:
				cmd = ['xdg-screensaver', 'suspend' if prevent else 'resume', str(frame.GetHandle())]
				subprocess.call(cmd)
			except:
				pass

class printWindowPlugin(wx.Frame):
	def __init__(self, parent, printerConnection, filename):
		super(printWindowPlugin, self).__init__(parent, -1, style=wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.CAPTION|wx.SYSTEM_MENU|wx.FRAME_FLOAT_ON_PARENT|wx.MINIMIZE_BOX, title=_("Printing on %s") % (printerConnection.getName()))
		self._printerConnection = printerConnection
		self._basePath = os.path.dirname(filename)
		self._backgroundImage = None
		self._colorCommandMap = {}
		self._buttonList = []
		self._termLog = None
		self._termInput = None
		self._termHistory = []
		self._termHistoryIdx = 0
		self._progressBar = None
		self._tempGraph = None
		self._infoText = None
		self._lastUpdateTime = time.time()
		self._isPrinting = False

		variables = {
			'setImage': self.script_setImage,
			'addColorCommand': self.script_addColorCommand,
			'addTerminal': self.script_addTerminal,
			'addTemperatureGraph': self.script_addTemperatureGraph,
			'addProgressbar': self.script_addProgressbar,
			'addButton': self.script_addButton,
			'addSpinner': self.script_addSpinner,
			'addTextButton': self.script_addTextButton,

			'sendGCode': self.script_sendGCode,
			'sendMovementGCode': self.script_sendMovementGCode,
			'connect': self.script_connect,
			'startPrint': self.script_startPrint,
			'pausePrint': self.script_pausePrint,
			'cancelPrint': self.script_cancelPrint,
			'showErrorLog': self.script_showErrorLog,
		}
		execfile(filename, variables, variables)

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		self.Bind(wx.EVT_PAINT, self.OnDraw)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftClick)
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		self._updateButtonStates()

		self._printerConnection.addCallback(self._doPrinterConnectionUpdate)

		if self._printerConnection.hasActiveConnection() and not self._printerConnection.isActiveConnectionOpen():
			self._printerConnection.openActiveConnection()

	def script_setImage(self, guiImage, mapImage):
		self._backgroundImage = wx.BitmapFromImage(wx.Image(os.path.join(self._basePath, guiImage)))
		self._mapImage = wx.Image(os.path.join(self._basePath, mapImage))
		self.SetClientSize(self._mapImage.GetSize())

	def script_addColorCommand(self, r, g, b, command, data = None):
		self._colorCommandMap[(r, g, b)] = (command, data)

	def script_addTerminal(self, r, g, b):
		x, y, w, h = self._getColoredRect(r, g, b)
		if x < 0 or self._termLog is not None:
			return
		f = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False)
		self._termLog = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_DONTWRAP)
		self._termLog.SetFont(f)
		self._termLog.SetEditable(0)
		self._termInput = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self._termInput.SetFont(f)

		self._termLog.SetPosition((x, y))
		self._termLog.SetSize((w, h - self._termInput.GetSize().GetHeight()))
		self._termInput.SetPosition((x, y + h - self._termInput.GetSize().GetHeight()))
		self._termInput.SetSize((w, self._termInput.GetSize().GetHeight()))
		self.Bind(wx.EVT_TEXT_ENTER, self.OnTermEnterLine, self._termInput)
		self._termInput.Bind(wx.EVT_CHAR, self.OnTermKey)

	def script_addTemperatureGraph(self, r, g, b):
		x, y, w, h = self._getColoredRect(r, g, b)
		if x < 0 or self._tempGraph is not None:
			return
		self._tempGraph = TemperatureGraph(self)

		self._tempGraph.SetPosition((x, y))
		self._tempGraph.SetSize((w, h))

	def script_addProgressbar(self, r, g, b):
		x, y, w, h = self._getColoredRect(r, g, b)
		if x < 0:
			return
		self._progressBar = wx.Gauge(self, -1, range=1000)

		self._progressBar.SetPosition((x, y))
		self._progressBar.SetSize((w, h))

	def script_addButton(self, r, g, b, text, command, data = None):
		x, y, w, h = self._getColoredRect(r, g, b)
		if x < 0:
			return
		button = wx.Button(self, -1, _(text))
		button.SetPosition((x, y))
		button.SetSize((w, h))
		button.command = command
		button.data = data
		self._buttonList.append(button)
		self.Bind(wx.EVT_BUTTON, lambda e: command(data), button)

	def script_addSpinner(self, r, g, b, command, data):
		x, y, w, h = self._getColoredRect(r, g, b)
		if x < 0:
			return

		def run_command(spinner):
			value = spinner.GetValue()
			print "Value (%s) and (%s)" % (spinner.last_value, value)
			if spinner.last_value != '' and value != 0:
				spinner.command(spinner.data % value)
				spinner.last_value = value

		spinner = wx.SpinCtrl(self, -1, style=wx.TE_PROCESS_ENTER)
		spinner.SetRange(0, 300)
		spinner.SetPosition((x, y))
		spinner.SetSize((w, h))
		spinner.SetValue(0)
		spinner.command = command
		spinner.data = data
		spinner.last_value = ''
		self._buttonList.append(spinner)
		self.Bind(wx.EVT_SPINCTRL, lambda e: run_command(spinner), spinner)

	def script_addTextButton(self, r_text, g_text, b_text, r_button, g_button, b_button, button_text, command, data):
		x_text, y_text, w_text, h_text = self._getColoredRect(r_text, g_text, b_text)
		if x_text < 0:
			return
		x_button, y_button, w_button, h_button = self._getColoredRect(r_button, g_button, b_button)
		if x_button < 0:
			return
		from wx.lib.intctrl import IntCtrl
		text = IntCtrl(self, -1)
		text.SetBounds(0, 300)
		text.SetPosition((x_text, y_text))
		text.SetSize((w_text, h_text))
		
		button = wx.Button(self, -1, _(button_text))
		button.SetPosition((x_button, y_button))
		button.SetSize((w_button, h_button))
		button.command = command
		button.data = data
		self._buttonList.append(button)
		self.Bind(wx.EVT_BUTTON, lambda e: command(data % text.GetValue()), button)

	def _getColoredRect(self, r, g, b):
		for x in xrange(0, self._mapImage.GetWidth()):
			for y in xrange(0, self._mapImage.GetHeight()):
				if self._mapImage.GetRed(x, y) == r and self._mapImage.GetGreen(x, y) == g and self._mapImage.GetBlue(x, y) == b:
					w = 0
					while x+w < self._mapImage.GetWidth() and self._mapImage.GetRed(x + w, y) == r and self._mapImage.GetGreen(x + w, y) == g and self._mapImage.GetBlue(x + w, y) == b:
						w += 1
					h = 0
					while y+h < self._mapImage.GetHeight() and self._mapImage.GetRed(x, y + h) == r and self._mapImage.GetGreen(x, y + h) == g and self._mapImage.GetBlue(x, y + h) == b:
						h += 1
					return x, y, w, h
		print "Failed to find color: ", r, g, b
		return -1, -1, 1, 1

	def script_sendGCode(self, data = None):
		for line in data.split(';'):
			line = line.strip()
			if len(line) > 0:
				self._printerConnection.sendCommand(line)

	def script_sendMovementGCode(self, data = None):
		if not self._printerConnection.isPaused() and not self._printerConnection.isPrinting():
			self.script_sendGCode(data)

	def script_connect(self, data = None):
		self._printerConnection.openActiveConnection()

	def script_startPrint(self, data = None):
		if self._printerConnection.isPrinting() or self._printerConnection.isPaused():
			self._printerConnection.pause(not self._printerConnection.isPaused())
		else:
			self._printerConnection.startPrint()

	def script_cancelPrint(self, e):
		self._printerConnection.cancelPrint()

	def script_pausePrint(self, e):
		self._printerConnection.pause(not self._printerConnection.isPaused())

	def script_showErrorLog(self, e):
		LogWindow(self._printerConnection.getErrorLog())

	def OnEraseBackground(self, e):
		pass

	def OnDraw(self, e):
		dc = wx.BufferedPaintDC(self, self._backgroundImage)

	def OnLeftClick(self, e):
		r = self._mapImage.GetRed(e.GetX(), e.GetY())
		g = self._mapImage.GetGreen(e.GetX(), e.GetY())
		b = self._mapImage.GetBlue(e.GetX(), e.GetY())
		if (r, g, b) in self._colorCommandMap:
			command = self._colorCommandMap[(r, g, b)]
			command[0](command[1])

	def OnClose(self, e):
		if self._printerConnection.hasActiveConnection():
			if self._printerConnection.isPrinting() or self._printerConnection.isPaused():
				pass #TODO: Give warning that the close will kill the print.
			self._printerConnection.closeActiveConnection()
		self._printerConnection.removeCallback(self._doPrinterConnectionUpdate)
		#TODO: When multiple printer windows are open, closing one will enable sleeping again.
		preventComputerFromSleeping(self, False)
		self._printerConnection.cancelPrint()
		self.Destroy()

	def OnTermEnterLine(self, e):
		if not self._printerConnection.isAbleToSendDirectCommand():
			return
		line = self._termInput.GetValue()
		if line == '':
			return
		self._addTermLog('> %s\n' % (line))
		self._printerConnection.sendCommand(line)
		self._termHistory.append(line)
		self._termHistoryIdx = len(self._termHistory)
		self._termInput.SetValue('')

	def OnTermKey(self, e):
		if len(self._termHistory) > 0:
			if e.GetKeyCode() == wx.WXK_UP:
				self._termHistoryIdx -= 1
				if self._termHistoryIdx < 0:
					self._termHistoryIdx = len(self._termHistory) - 1
				self._termInput.SetValue(self._termHistory[self._termHistoryIdx])
				return
			if e.GetKeyCode() == wx.WXK_DOWN:
				self._termHistoryIdx -= 1
				if self._termHistoryIdx >= len(self._termHistory):
					self._termHistoryIdx = 0
				self._termInput.SetValue(self._termHistory[self._termHistoryIdx])
				return
		e.Skip()

	def _addTermLog(self, line):
		if self._termLog is not None:
			if len(self._termLog.GetValue()) > 10000:
				self._termLog.SetValue(self._termLog.GetValue()[-10000:])
			self._termLog.SetInsertionPointEnd()
			if type(line) != unicode:
				line = unicode(line, 'utf-8', 'replace')
			self._termLog.AppendText(line.encode('utf-8', 'replace'))

	def _updateButtonStates(self):
		hasPauseButton = False
		for button in self._buttonList:
			if button.command == self.script_pausePrint:
				hasPauseButton = True
				break

		for button in self._buttonList:
			if button.command == self.script_connect:
				button.Show(self._printerConnection.hasActiveConnection())
				button.Enable(not self._printerConnection.isActiveConnectionOpen() and \
							  not self._printerConnection.isActiveConnectionOpening())
			elif button.command == self.script_pausePrint:
				button.Show(self._printerConnection.hasPause())
				if not self._printerConnection.hasActiveConnection() or \
				   self._printerConnection.isActiveConnectionOpen():
					button.Enable(self._printerConnection.isPrinting() or \
								  self._printerConnection.isPaused())
					if self._printerConnection.isPaused():
						button.SetLabel(_("Resume"))
					else:
						button.SetLabel(_("Pause"))
				else:
					button.Enable(False)
			elif button.command == self.script_startPrint:
				if hasPauseButton or not self._printerConnection.hasPause():
					if not self._printerConnection.hasActiveConnection() or \
					   self._printerConnection.isActiveConnectionOpen():
							button.Enable(not self._printerConnection.isPrinting() and \
										  not self._printerConnection.isPaused())
					else:
						button.Enable(False)
				else:
					if not self._printerConnection.hasActiveConnection() or \
					   self._printerConnection.isActiveConnectionOpen():
						if self._printerConnection.isPrinting():
							if self.pauseTimer.IsRunning():
								self.printButton.Enable(False)
								self.printButton.SetLabel(_("Please wait..."))
							else:
								self.printButton.Enable(True)
								button.SetLabel(_("Pause"))
						else:
							if self._printerConnection.isPaused():
								if self.pauseTimer.IsRunning():
									self.printButton.Enable(False)
									self.printButton.SetLabel(_("Please wait..."))
								else:
									self.printButton.Enable(True)
									button.SetLabel(_("Resume"))
							else:
								button.SetLabel(_("Print"))
								button.Enable(True)
								self.pauseTimer.Stop()
					else:
						button.Enable(False)
			elif button.command == self.script_cancelPrint:
				if not self._printerConnection.hasActiveConnection() or \
				   self._printerConnection.isActiveConnectionOpen():
					button.Enable(self._printerConnection.isPrinting() or \
								  self._printerConnection.isPaused())
				else:
					button.Enable(False)
			elif button.command == self.script_showErrorLog:
				button.Show(self._printerConnection.isInErrorState())
		if self._termInput is not None:
			self._termInput.Enable(self._printerConnection.isAbleToSendDirectCommand())

	def _doPrinterConnectionUpdate(self, connection, extraInfo = None):
		wx.CallAfter(self.__doPrinterConnectionUpdate, connection, extraInfo)
		if self._tempGraph is not None:
			temp = []
			for n in xrange(0, 4):
				t = connection.getTemperature(0)
				if t is not None:
					temp.append(t)
				else:
					break
			self._tempGraph.addPoint(temp, [0] * len(temp), connection.getBedTemperature(), 0)

	def __doPrinterConnectionUpdate(self, connection, extraInfo):
		t = time.time()
		if self._lastUpdateTime + 0.5 > t and extraInfo is None:
			return
		self._lastUpdateTime = t

		if extraInfo is not None and len(extraInfo) > 0:
			self._addTermLog('< %s\n' % (extraInfo))

		self._updateButtonStates()
		isPrinting = connection.isPrinting() or connection.isPaused()
		if self._progressBar is not None:
			if isPrinting:
				(current, total, z) = connection.getPrintProgress()
				progress = 0.0
				if total > 0:
					progress = float(current) / float(total)
				self._progressBar.SetValue(progress * 1000)
			else:
				self._progressBar.SetValue(0)
		info = connection.getStatusString()
		info += '\n'
		if self._printerConnection.getTemperature(0) is not None:
			info += 'Temperature: %d' % (self._printerConnection.getTemperature(0))
		if self._printerConnection.getBedTemperature() > 0:
			info += ' Bed: %d' % (self._printerConnection.getBedTemperature())
		if self._infoText is not None:
			self._infoText.SetLabel(info)
		else:
			self.SetTitle(info.replace('\n', ', ').strip(', '))
		if isPrinting != self._isPrinting:
			self._isPrinting = isPrinting
			preventComputerFromSleeping(self, self._isPrinting)

class printWindowBasic(wx.Frame):
	"""
	Printing window for USB printing, network printing, and any other type of printer connection we can think off.
	This is only a basic window with minimal information.
	"""
	def __init__(self, parent, printerConnection):
		super(printWindowBasic, self).__init__(parent, -1, style=wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.CAPTION|wx.SYSTEM_MENU|wx.FRAME_TOOL_WINDOW|wx.FRAME_FLOAT_ON_PARENT, title=_("Printing on %s") % (printerConnection.getName()))
		self._printerConnection = printerConnection
		self._lastUpdateTime = 0
		self._isPrinting = False

		self.SetSizer(wx.BoxSizer())
		self.panel = wx.Panel(self)
		self.GetSizer().Add(self.panel, 1, flag=wx.EXPAND)
		self.sizer = wx.GridBagSizer(2, 2)
		self.panel.SetSizer(self.sizer)

		self.powerWarningText = wx.StaticText(parent=self.panel,
			id=-1,
			label=_("Your computer is running on battery power.\nConnect your computer to AC power or your print might not finish."),
			style=wx.ALIGN_CENTER)
		self.powerWarningText.SetBackgroundColour('red')
		self.powerWarningText.SetForegroundColour('white')
		if power:
			self.powerManagement = power.PowerManagement()
		else:
			self.powerManagement = None
		self.powerWarningTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnPowerWarningChange, self.powerWarningTimer)
		self.OnPowerWarningChange(None)
		self.powerWarningTimer.Start(10000)

		self.statsText = wx.StaticText(self.panel, -1, _("InfoLine from printer connection\nInfoLine from dialog\nExtra line\nMore lines for layout\nMore lines for layout\nMore lines for layout"))

		self.connectButton = wx.Button(self.panel, -1, _("Connect"))
		#self.loadButton = wx.Button(self.panel, -1, 'Load')
		self.printButton = wx.Button(self.panel, -1, _("Print"))
		self.pauseButton = wx.Button(self.panel, -1, _("Pause"))
		self.cancelButton = wx.Button(self.panel, -1, _("Cancel print"))
		self.errorLogButton = wx.Button(self.panel, -1, _("Error log"))
		self.progress = wx.Gauge(self.panel, -1, range=1000)

		self.pauseTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnPauseTimer, self.pauseTimer)

		self.sizer.Add(self.powerWarningText, pos=(0, 0), span=(1, 5), flag=wx.EXPAND|wx.BOTTOM, border=5)
		self.sizer.Add(self.statsText, pos=(1, 0), span=(1, 5), flag=wx.LEFT, border=5)
		self.sizer.Add(self.connectButton, pos=(2, 0))
		#self.sizer.Add(self.loadButton, pos=(2,1))
		self.sizer.Add(self.printButton, pos=(2, 1))
		self.sizer.Add(self.pauseButton, pos=(2, 2))
		self.sizer.Add(self.cancelButton, pos=(2, 3))
		self.sizer.Add(self.errorLogButton, pos=(2, 4))
		self.sizer.Add(self.progress, pos=(3, 0), span=(1, 5), flag=wx.EXPAND)

		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.connectButton.Bind(wx.EVT_BUTTON, self.OnConnect)
		#self.loadButton.Bind(wx.EVT_BUTTON, self.OnLoad)
		self.printButton.Bind(wx.EVT_BUTTON, self.OnPrint)
		self.pauseButton.Bind(wx.EVT_BUTTON, self.OnPause)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)
		self.errorLogButton.Bind(wx.EVT_BUTTON, self.OnErrorLog)

		self.Layout()
		self.Fit()
		self.Centre()

		self.progress.SetMinSize(self.progress.GetSize())
		self.statsText.SetLabel('\n\n\n\n\n\n')
		self._updateButtonStates()

		self._printerConnection.addCallback(self._doPrinterConnectionUpdate)

		if self._printerConnection.hasActiveConnection() and not self._printerConnection.isActiveConnectionOpen():
			self._printerConnection.openActiveConnection()

	def OnPowerWarningChange(self, e):
		if self.powerManagement is None:
			return
		type = self.powerManagement.get_providing_power_source_type()
		if type == power.POWER_TYPE_AC and self.powerWarningText.IsShown():
			self.powerWarningText.Hide()
			self.panel.Layout()
			self.Layout()
			self.Fit()
			self.Refresh()
		elif type != power.POWER_TYPE_AC and not self.powerWarningText.IsShown():
			self.powerWarningText.Show()
			self.panel.Layout()
			self.Layout()
			self.Fit()
			self.Refresh()

	def OnClose(self, e):
		if self._printerConnection.hasActiveConnection():
			if self._printerConnection.isPrinting() or self._printerConnection.isPaused():
				pass #TODO: Give warning that the close will kill the print.
			self._printerConnection.closeActiveConnection()
		self._printerConnection.removeCallback(self._doPrinterConnectionUpdate)
		#TODO: When multiple printer windows are open, closing one will enable sleeping again.
		preventComputerFromSleeping(self, False)
		self.powerWarningTimer.Stop()
		self.pauseTimer.Stop()
		self.Destroy()

	def OnConnect(self, e):
		self._printerConnection.openActiveConnection()

	def OnLoad(self, e):
		pass

	def OnPrint(self, e):
		self._printerConnection.startPrint()

	def OnCancel(self, e):
		self._printerConnection.cancelPrint()

	def OnPause(self, e):
		self._printerConnection.pause(not self._printerConnection.isPaused())
		self.pauseButton.Enable(False)
		self.pauseTimer.Stop()
		self.pauseTimer.Start(10000)

	def OnPauseTimer(self, e):
		self.pauseButton.Enable(True)
		self.pauseTimer.Stop()
		self._updateButtonStates()

	def OnErrorLog(self, e):
		LogWindow(self._printerConnection.getErrorLog())

	def _doPrinterConnectionUpdate(self, connection, extraInfo = None):
		wx.CallAfter(self.__doPrinterConnectionUpdate, connection, extraInfo)
		#temp = [connection.getTemperature(0)]
		#self.temperatureGraph.addPoint(temp, [0], connection.getBedTemperature(), 0)

	def __doPrinterConnectionUpdate(self, connection, extraInfo):
		now = time.time()
		if self._lastUpdateTime + 0.5 > now and extraInfo is None:
			return
		self._lastUpdateTime = now

		if extraInfo is not None and len(extraInfo) > 0:
			self._addTermLog('< %s\n' % (extraInfo))

		self._updateButtonStates()
		onGoingPrint = connection.isPrinting() or connection.isPaused()
		if onGoingPrint:
			(current, total, z) = connection.getPrintProgress()
			progress = 0.0
			if total > 0:
				progress = float(current) / float(total)
			self.progress.SetValue(progress * 1000)
		else:
			self.progress.SetValue(0)
		info = connection.getStatusString()
		info += '\n'
		if self._printerConnection.getTemperature(0) is not None:
			info += 'Temperature: %d' % (self._printerConnection.getTemperature(0))
		if self._printerConnection.getBedTemperature() > 0:
			info += ' Bed: %d' % (self._printerConnection.getBedTemperature())
		info += '\n\n'
		self.statsText.SetLabel(info)
		if onGoingPrint != self._isPrinting:
			self._isPrinting = onGoingPrint
			preventComputerFromSleeping(self, self._isPrinting)

	def _addTermLog(self, msg):
		pass

	def _updateButtonStates(self):
		self.connectButton.Show(self._printerConnection.hasActiveConnection())
		self.connectButton.Enable(not self._printerConnection.isActiveConnectionOpen() and not self._printerConnection.isActiveConnectionOpening())
		self.pauseButton.Show(self._printerConnection.hasPause())
		if not self._printerConnection.hasActiveConnection() or self._printerConnection.isActiveConnectionOpen():
			self.printButton.Enable(not self._printerConnection.isPrinting() and \
									not self._printerConnection.isPaused())
			self.pauseButton.Enable(self._printerConnection.isPrinting())
			self.cancelButton.Enable(self._printerConnection.isPrinting())
		else:
			self.printButton.Enable(False)
			self.pauseButton.Enable(False)
			self.cancelButton.Enable(False)
		self.errorLogButton.Show(self._printerConnection.isInErrorState())

class printWindowAdvanced(wx.Frame):
	def __init__(self, parent, printerConnection):
		super(printWindowAdvanced, self).__init__(parent, -1, style=wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.CAPTION|wx.SYSTEM_MENU|wx.FRAME_FLOAT_ON_PARENT|wx.MINIMIZE_BOX, title=_("Printing on %s") % (printerConnection.getName()))
		self._printerConnection = printerConnection
		self._lastUpdateTime = time.time()
		self._printDuration = 0
		self._lastDurationTime = None
		self._isPrinting = False

		self.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.toppanel = wx.Panel(self)
		self.topsizer = wx.GridBagSizer(2, 2)
		self.toppanel.SetSizer(self.topsizer)
		self.toppanel.SetBackgroundColour(wx.WHITE)
		self.topsizer.SetEmptyCellSize((125, 1))
		self.panel = wx.Panel(self)
		self.sizer = wx.GridBagSizer(2, 2)
		self.sizer.SetEmptyCellSize((125, 1))
		self.panel.SetSizer(self.sizer)
		self.panel.SetBackgroundColour(wx.WHITE)
		self.GetSizer().Add(self.toppanel, 0, flag=wx.EXPAND)
		self.GetSizer().Add(self.panel, 1, flag=wx.EXPAND)

		self._fullscreenTemperature = None
		self._termHistory = []
		self._termHistoryIdx = 0

		self._mapImage = wx.Image(resources.getPathForImage('print-window-map.png'))
		self._colorCommandMap = {}

		# Move X
		self._addMovementCommand(0, 0, 255, self._moveX, 100)
		self._addMovementCommand(0, 0, 240, self._moveX, 10)
		self._addMovementCommand(0, 0, 220, self._moveX, 1)
		self._addMovementCommand(0, 0, 200, self._moveX, 0.1)
		self._addMovementCommand(0, 0, 180, self._moveX, -0.1)
		self._addMovementCommand(0, 0, 160, self._moveX, -1)
		self._addMovementCommand(0, 0, 140, self._moveX, -10)
		self._addMovementCommand(0, 0, 120, self._moveX, -100)

		# Move Y
		self._addMovementCommand(0, 255, 0, self._moveY, -100)
		self._addMovementCommand(0, 240, 0, self._moveY, -10)
		self._addMovementCommand(0, 220, 0, self._moveY, -1)
		self._addMovementCommand(0, 200, 0, self._moveY, -0.1)
		self._addMovementCommand(0, 180, 0, self._moveY, 0.1)
		self._addMovementCommand(0, 160, 0, self._moveY, 1)
		self._addMovementCommand(0, 140, 0, self._moveY, 10)
		self._addMovementCommand(0, 120, 0, self._moveY, 100)

		# Move Z
		self._addMovementCommand(255, 0, 0, self._moveZ, 10)
		self._addMovementCommand(220, 0, 0, self._moveZ, 1)
		self._addMovementCommand(200, 0, 0, self._moveZ, 0.1)
		self._addMovementCommand(180, 0, 0, self._moveZ, -0.1)
		self._addMovementCommand(160, 0, 0, self._moveZ, -1)
		self._addMovementCommand(140, 0, 0, self._moveZ, -10)

		# Extrude/Retract
		self._addMovementCommand(255, 80, 0, self._moveE, 10)
		self._addMovementCommand(255, 180, 0, self._moveE, -10)

		# Home
		self._addMovementCommand(255, 255, 0, self._homeXYZ, None)
		self._addMovementCommand(240, 255, 0, self._homeXYZ, "X")
		self._addMovementCommand(220, 255, 0, self._homeXYZ, "Y")
		self._addMovementCommand(200, 255, 0, self._homeXYZ, "Z")

		self.powerWarningText = wx.StaticText(parent=self.toppanel,
			id=-1,
			label=_("Your computer is running on battery power.\nConnect your computer to AC power or your print might not finish."),
			style=wx.ALIGN_CENTER)
		self.powerWarningText.SetBackgroundColour('red')
		self.powerWarningText.SetForegroundColour('white')
		if power:
			self.powerManagement = power.PowerManagement()
		else:
			self.powerManagement = None
		self.powerWarningTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnPowerWarningChange, self.powerWarningTimer)
		self.OnPowerWarningChange(None)
		self.powerWarningTimer.Start(10000)

		self.pauseTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnPauseTimer, self.pauseTimer)

		self.connectButton = wx.Button(self.toppanel, -1, _("Connect"), size=(125, 30))
		self.printButton = wx.Button(self.toppanel, -1, _("Print"), size=(125, 30))
		self.cancelButton = wx.Button(self.toppanel, -1, _("Cancel"), size=(125, 30))
		self.errorLogButton = wx.Button(self.toppanel, -1, _("Error log"), size=(125, 30))
		self.motorsOffButton = wx.Button(self.toppanel, -1, _("Motors off"), size=(125, 30))
		self.movementBitmap = wx.StaticBitmap(self.panel, -1, wx.BitmapFromImage(wx.Image(
				resources.getPathForImage('print-window.png'))), (0, 0))
		self.temperatureBitmap = wx.StaticBitmap(self.panel, -1, wx.BitmapFromImage(wx.Image(
				resources.getPathForImage('print-window-temperature.png'))), (0, 0))
		self.temperatureField = TemperatureField(self.panel, self._setHotendTemperature)
		self.temperatureBedBitmap = wx.StaticBitmap(self.panel, -1, wx.BitmapFromImage(wx.Image(
				resources.getPathForImage('print-window-temperature-bed.png'))), (0, 0))
		self.temperatureBedField = TemperatureField(self.panel, self._setBedTemperature)
		self.temperatureGraph = TemperatureGraph(self.panel)
		self.temperatureGraph.SetMinSize((250, 100))
		self.progress = wx.Gauge(self.panel, -1, range=1000)

		f = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False)
		self._termLog = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
		self._termLog.SetFont(f)
		self._termLog.SetEditable(0)
		self._termLog.SetMinSize((385, -1))
		self._termInput = wx.TextCtrl(self.panel, style=wx.TE_PROCESS_ENTER)
		self._termInput.SetFont(f)

		self.Bind(wx.EVT_TEXT_ENTER, self.OnTermEnterLine, self._termInput)
		self._termInput.Bind(wx.EVT_CHAR, self.OnTermKey)

		self.topsizer.Add(self.powerWarningText, pos=(0, 0), span=(1, 6), flag=wx.EXPAND|wx.BOTTOM, border=5)
		self.topsizer.Add(self.connectButton, pos=(1, 0), flag=wx.LEFT, border=2)
		self.topsizer.Add(self.printButton, pos=(1, 1), flag=wx.LEFT, border=2)
		self.topsizer.Add(self.cancelButton, pos=(1, 2), flag=wx.LEFT, border=2)
		self.topsizer.Add(self.errorLogButton, pos=(1, 4), flag=wx.LEFT, border=2)
		self.topsizer.Add(self.motorsOffButton, pos=(1, 5), flag=wx.LEFT|wx.RIGHT, border=2)
		self.sizer.Add(self.movementBitmap, pos=(0, 0), span=(2, 3))
		self.sizer.Add(self.temperatureGraph, pos=(2, 0), span=(4, 2), flag=wx.EXPAND)
		self.sizer.Add(self.temperatureBitmap, pos=(2, 2))
		self.sizer.Add(self.temperatureField, pos=(3, 2))
		self.sizer.Add(self.temperatureBedBitmap, pos=(4, 2))
		self.sizer.Add(self.temperatureBedField, pos=(5, 2))
		self.sizer.Add(self._termLog, pos=(0, 3), span=(5, 3), flag=wx.EXPAND|wx.RIGHT, border=5)
		self.sizer.Add(self._termInput, pos=(5, 3), span=(1, 3), flag=wx.EXPAND|wx.RIGHT, border=5)
		self.sizer.Add(self.progress, pos=(7, 0), span=(1, 6), flag=wx.EXPAND|wx.BOTTOM)

		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.movementBitmap.Bind(wx.EVT_LEFT_DOWN, self.OnMovementClick)
		self.temperatureGraph.Bind(wx.EVT_LEFT_UP, self.OnTemperatureClick)
		self.connectButton.Bind(wx.EVT_BUTTON, self.OnConnect)
		self.printButton.Bind(wx.EVT_BUTTON, self.OnPrint)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)
		self.errorLogButton.Bind(wx.EVT_BUTTON, self.OnErrorLog)
		self.motorsOffButton.Bind(wx.EVT_BUTTON, self.OnMotorsOff)

		self.Layout()
		self.Fit()
		self.Refresh()
		self.progress.SetMinSize(self.progress.GetSize())
		self._updateButtonStates()

		self._printerConnection.addCallback(self._doPrinterConnectionUpdate)

		if self._printerConnection.hasActiveConnection() and \
		   not self._printerConnection.isActiveConnectionOpen():
			self._printerConnection.openActiveConnection()

	def OnSize(self, e):
		# HACK ALERT: This is needed for some reason otherwise the window
		# will be bigger than it should be until a power warning change
		self.Layout()
		self.Fit()
		e.Skip()

	def OnClose(self, e):
		if self._printerConnection.hasActiveConnection():
			if self._printerConnection.isPrinting() or self._printerConnection.isPaused():
				pass #TODO: Give warning that the close will kill the print.
			self._printerConnection.closeActiveConnection()
		self._printerConnection.removeCallback(self._doPrinterConnectionUpdate)
		#TODO: When multiple printer windows are open, closing one will enable sleeping again.
		preventComputerFromSleeping(self, False)
		self._printerConnection.cancelPrint()
		self.powerWarningTimer.Stop()
		self.pauseTimer.Stop()
		self.Destroy()

	def OnPowerWarningChange(self, e):
		if self.powerManagement is None:
			return
		type = self.powerManagement.get_providing_power_source_type()
		if type == power.POWER_TYPE_AC and self.powerWarningText.IsShown():
			self.powerWarningText.Hide()
			self.toppanel.Layout()
			self.Layout()
			self.Fit()
			self.Refresh()
		elif type != power.POWER_TYPE_AC and not self.powerWarningText.IsShown():
			self.powerWarningText.Show()
			self.toppanel.Layout()
			self.Layout()
			self.Fit()
			self.Refresh()

	def OnConnect(self, e):
		self._printerConnection.openActiveConnection()

	def OnPrint(self, e):
		if self._printerConnection.isPrinting() or self._printerConnection.isPaused():
			if self._printerConnection.isPaused():
				self._addTermLog(_("Print resumed at %s\n") % (time.strftime(TIME_FORMAT)))
				self._lastDurationTime = time.time()
			else:
				self._addTermLog(_("Print paused at %s\n") % (time.strftime(TIME_FORMAT)))
				self._printDuration = self._printDuration + (time.time() - self._lastDurationTime)
				self._lastDurationTime = None
			self._printerConnection.pause(not self._printerConnection.isPaused())
			self.pauseTimer.Stop()
			self.printButton.Enable(False)
			self.pauseTimer.Start(10000)
		else:
			self._printerConnection.startPrint()
			self._addTermLog(_("Print started at %s\n") % (time.strftime(TIME_FORMAT)))
			self._printDuration = 0
			self._lastDurationTime = time.time()


	def _printFinished(self):
		duration = self._printDuration
		if self._lastDurationTime:
				duration += (time.time() - self._lastDurationTime)
		m, s = divmod(duration, 60)
		h, m = divmod(m, 60)
		self._printDuration = 0
		self._lastDurationTime = None
		self._addTermLog(_("Total print time : %d:%02d:%02d\n") % (h, m, s))

	def OnPauseTimer(self, e):
		self.printButton.Enable(True)
		self.pauseTimer.Stop()
		self._updateButtonStates()

	def OnCancel(self, e):
		self._printerConnection.cancelPrint()
		self._addTermLog(_("Print canceled at %s\n") % (time.strftime(TIME_FORMAT)))
		self._printFinished()

	def OnErrorLog(self, e):
		LogWindow(self._printerConnection.getErrorLog())

	def OnMotorsOff(self, e):
		self._printerConnection.sendCommand("M18")

	def GetMapRGB(self, x, y):
		r = self._mapImage.GetRed(x, y)
		g = self._mapImage.GetGreen(x, y)
		b = self._mapImage.GetBlue(x, y)
		return (r, g, b)

	def OnMovementClick(self, e):
		(r, g, b) = self.GetMapRGB(e.GetX(), e.GetY())
		if (r, g, b) in self._colorCommandMap:
			command = self._colorCommandMap[(r, g, b)]
			command[0](command[1])

	def _addMovementCommand(self, r, g, b, command, step):
		self._colorCommandMap[(r, g, b)] = (command, step)

	def _moveXYZE(self, motor, step, feedrate):
		# Prevent Z movement when paused and all moves when printing
		if (not self._printerConnection.hasActiveConnection() or \
			self._printerConnection.isActiveConnectionOpen()) and \
			(not (self._printerConnection.isPaused() and motor != 'E') and \
			 not self._printerConnection.isPrinting()):
			self._printerConnection.sendCommand("G91")
			self._printerConnection.sendCommand("G1 %s%.1f F%d" % (motor, step, feedrate))
			self._printerConnection.sendCommand("G90")

	def _moveX(self, step):
		self._moveXYZE("X", step, 2000)

	def _moveY(self, step):
		self._moveXYZE("Y", step, 2000)

	def _moveZ(self, step):
		self._moveXYZE("Z", step, 200)

	def _moveE(self, step):
		feedrate = 120
		if "lulzbot_" in profile.getMachineSetting("machine_type"):
			toolhead_name = profile.getMachineSetting("toolhead")
			toolhead_name = toolhead_name.lower()
			if "flexy" in toolhead_name:
				feedrate = 30
		self._moveXYZE("E", step, feedrate)

	def _homeXYZ(self, direction):
		if not self._printerConnection.isPaused() and not self._printerConnection.isPrinting():
			if direction is None:
				self._printerConnection.sendCommand("G28")
			else:
				self._printerConnection.sendCommand("G28 %s0" % direction)

	def _setHotendTemperature(self, value):
		self._printerConnection.sendCommand("M104 S%d" % value)

	def _setBedTemperature(self, value):
		self._printerConnection.sendCommand("M140 S%d" % value)

	def OnTemperatureClick(self, e):
		wx.CallAfter(self.ToggleFullScreenTemperature)

	def ToggleFullScreenTemperature(self):
		sizer = self.GetSizer()
		if self._fullscreenTemperature:
			self._fullscreenTemperature.Show(False)
			sizer.Detach(self._fullscreenTemperature)
			self._fullscreenTemperature.Destroy()
			self._fullscreenTemperature = None
			self.panel.Show(True)
		else:
			self._fullscreenTemperature = self.temperatureGraph.Clone(self)
			self._fullscreenTemperature.Bind(wx.EVT_LEFT_UP, self.OnTemperatureClick)
			self._fullscreenTemperature.SetMinSize(self.panel.GetSize())
			sizer.Add(self._fullscreenTemperature, 1, flag=wx.EXPAND)
			self.panel.Show(False)
		self.Layout()
		self.Refresh()

	def OnTermEnterLine(self, e):
		if not self._printerConnection.isAbleToSendDirectCommand():
			return
		line = self._termInput.GetValue()
		if line == '':
			return
		self._addTermLog('> %s\n' % (line))
		self._printerConnection.sendCommand(line)
		self._termHistory.append(line)
		self._termHistoryIdx = len(self._termHistory)
		self._termInput.SetValue('')

	def OnTermKey(self, e):
		if len(self._termHistory) > 0:
			if e.GetKeyCode() == wx.WXK_UP:
				self._termHistoryIdx -= 1
				if self._termHistoryIdx < 0:
					self._termHistoryIdx = len(self._termHistory) - 1
				self._termInput.SetValue(self._termHistory[self._termHistoryIdx])
				return
			if e.GetKeyCode() == wx.WXK_DOWN:
				self._termHistoryIdx -= 1
				if self._termHistoryIdx >= len(self._termHistory):
					self._termHistoryIdx = 0
				self._termInput.SetValue(self._termHistory[self._termHistoryIdx])
				return
		e.Skip()

	def _addTermLog(self, line):
		if self._termLog is not None:
			if len(self._termLog.GetValue()) > 10000:
				self._termLog.SetValue(self._termLog.GetValue()[-10000:])
			self._termLog.SetInsertionPointEnd()
			if type(line) != unicode:
				line = unicode(line, 'utf-8', 'replace')
			self._termLog.AppendText(line.encode('utf-8', 'replace'))

	def _updateButtonStates(self):
		self.connectButton.Show(self._printerConnection.hasActiveConnection())
		self.connectButton.Enable(not self._printerConnection.isActiveConnectionOpen() and \
								  not self._printerConnection.isActiveConnectionOpening())
		if not self._printerConnection.hasPause():
			if not self._printerConnection.hasActiveConnection() or \
			   self._printerConnection.isActiveConnectionOpen():
				self.printButton.Enable(not self._printerConnection.isPrinting() and \
										not self._printerConnection.isPaused())
			else:
				self.printButton.Enable(False)
		else:
			if not self._printerConnection.hasActiveConnection() or \
			   self._printerConnection.isActiveConnectionOpen():
				if self._printerConnection.isPrinting():
					if self.pauseTimer.IsRunning():
						self.printButton.Enable(False)
						self.printButton.SetLabel(_("Please wait..."))
					else:
						self.printButton.Enable(True)
						self.printButton.SetLabel(_("Pause"))
				else:
					if self._printerConnection.isPaused():
						if self.pauseTimer.IsRunning():
							self.printButton.Enable(False)
							self.printButton.SetLabel(_("Please wait..."))
						else:
							self.printButton.SetLabel(_("Resume"))
							self.printButton.Enable(True)
					else:
						self.printButton.SetLabel(_("Print"))
						self.printButton.Enable(True)
						self.pauseTimer.Stop()
			else:
				self.printButton.Enable(False)
		if not self._printerConnection.hasActiveConnection() or \
		   self._printerConnection.isActiveConnectionOpen():
			self.cancelButton.Enable(self._printerConnection.isPrinting() or \
									 self._printerConnection.isPaused())
		else:
			self.cancelButton.Enable(False)
		if version.isDevVersion():
			if self._printerConnection.isInErrorState():
				self.errorLogButton.SetLabel(_("Error Log"))
			else:
				self.errorLogButton.SetLabel(_("Show Log"))
		else:
			self.errorLogButton.Show(self._printerConnection.isInErrorState())
		self._termInput.Enable(self._printerConnection.isAbleToSendDirectCommand())
		self.Layout()

	def _doPrinterConnectionUpdate(self, connection, extraInfo = None):
		wx.CallAfter(self.__doPrinterConnectionUpdate, connection, extraInfo)
		temp = []
		for n in xrange(0, 4):
			t = connection.getTemperature(0)
			if t is not None:
				temp.append(t)
			else:
				break
		self.temperatureGraph.addPoint(temp, [0] * len(temp), connection.getBedTemperature(), 0)
		if self._fullscreenTemperature is not None:
			self._fullscreenTemperature.addPoint(temp, [0] * len(temp), connection.getBedTemperature(), 0)

	def __doPrinterConnectionUpdate(self, connection, extraInfo):
		t = time.time()
		if self._lastUpdateTime + 0.5 > t and extraInfo is None:
			return
		self._lastUpdateTime = t

		if extraInfo is not None and len(extraInfo) > 0:
			self._addTermLog('< %s\n' % (extraInfo))

		self._updateButtonStates()
		
		info = connection.getStatusString()
		isPrinting = connection.isPrinting() or connection.isPaused()
		if isPrinting:
			(current, total, z) = connection.getPrintProgress()
			progress = 0.0
			if total > 0:
				progress = float(current) / float(total)
			self.progress.SetValue(progress * 1000)
			info += (" {:3.1f}% | ".format(progress * 100))
			info += (("Z: %.3fmm") % (z))
		else:
			# Should be 1000 but doesn't always seem to work,so check for 90%+ in the
			# progress bar (before it gets reset to 0) and check the actual progress for 100%
			if self.progress.GetValue() >= 900:
				(current, total, z) = connection.getPrintProgress()
				if current >= total:
					self._addTermLog(_("Print finished at %s\n") % (time.strftime(TIME_FORMAT)))
					self._printFinished()
			self.progress.SetValue(0)

		if self._printDuration > 0 or self._lastDurationTime != None:
			duration = self._printDuration
			if self._lastDurationTime:
				duration += (time.time() - self._lastDurationTime)
			m, s = divmod(duration, 60)
			h, m = divmod(m, 60)
			if h > 0:
				info += ' | Printing for : %d:%02d:%02d ' % (h, m, s)
			else:
				info += ' | Printing for : %d:%02d ' % (m, s)
		if self._printerConnection.getTemperature(0) is not None:
			info += ' | Temperature: %d ' % (self._printerConnection.getTemperature(0))
		if self._printerConnection.getBedTemperature() > 0:
			info += 'Bed: %d' % (self._printerConnection.getBedTemperature())
		self.SetTitle(info.replace('\n', ', ').strip(', '))
		if isPrinting != self._isPrinting:
			self._isPrinting = isPrinting
			preventComputerFromSleeping(self, self._isPrinting)

class TemperatureField(wx.Panel):
	def __init__(self, parent, callback):
		super(TemperatureField, self).__init__(parent)
		self.callback = callback

		self.SetBackgroundColour(wx.WHITE)

		self.text = IntCtrl(self, -1)
		self.text.SetBounds(0, 300)
		self.text.SetSize((60, 28))

		self.unit = wx.StaticBitmap(self, -1, wx.BitmapFromImage(wx.Image(
				resources.getPathForImage('print-window-temperature-unit.png'))), (0, 0))

		self.button = wx.Button(self, -1, _("Set"))
		self.button.SetSize((35, 25))
		self.Bind(wx.EVT_BUTTON, lambda e: self.callback(self.text.GetValue()), self.button)

		self.text.SetPosition((0, 0))
		self.unit.SetPosition((60, 0))
		self.button.SetPosition((90, 0))


class TemperatureGraph(wx.Panel):
	def __init__(self, parent):
		super(TemperatureGraph, self).__init__(parent)

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_PAINT, self.OnDraw)

		self._lastDraw = time.time() - 1.0
		self._points = []
		self._backBuffer = None
		self.addPoint([0]*16, [0]*16, 0, 0)

	def Clone(self, parent):
		clone = TemperatureGraph(parent)
		clone._points = list(self._points)
		return clone

	def OnEraseBackground(self, e):
		pass

	def OnSize(self, e):
		if self._backBuffer is None or self.GetSize() != self._backBuffer.GetSize():
			self._backBuffer = wx.EmptyBitmap(*self.GetSizeTuple())
			self.UpdateDrawing(True)

	def OnDraw(self, e):
		dc = wx.BufferedPaintDC(self, self._backBuffer)

	def UpdateDrawing(self, force=False):
		now = time.time()
		if (not force and now - self._lastDraw < 1.0) or self._backBuffer is None:
			return
		self._lastDraw = now
		dc = wx.MemoryDC()
		dc.SelectObject(self._backBuffer)
		dc.SetBackground(wx.Brush(wx.WHITE))
		dc.Clear()
		dc.SetFont(wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT))
		w, h = self.GetSizeTuple()
		bgLinePen = wx.Pen('#A0A0A0')
		tempPen = wx.Pen('#FF4040')
		tempSPPen = wx.Pen('#FFA0A0')
		tempPenBG = wx.Pen('#FFD0D0')
		bedTempPen = wx.Pen('#4040FF')
		bedTempSPPen = wx.Pen('#A0A0FF')
		bedTempPenBG = wx.Pen('#D0D0FF')

		#Draw the background up to the current temperatures.
		x0 = 0
		t0 = []
		bt0 = 0
		tSP0 = 0
		btSP0 = 0
		for temp, tempSP, bedTemp, bedTempSP, t in self._points:
			x1 = int(w - (now - t))
			for x in xrange(x0, x1 + 1):
				for n in xrange(0, min(len(t0), len(temp))):
					t = float(x - x0) / float(x1 - x0 + 1) * (temp[n] - t0[n]) + t0[n]
					dc.SetPen(tempPenBG)
					dc.DrawLine(x, h, x, h - (t * h / 350))
				bt = float(x - x0) / float(x1 - x0 + 1) * (bedTemp - bt0) + bt0
				dc.SetPen(bedTempPenBG)
				dc.DrawLine(x, h, x, h - (bt * h / 350))
			t0 = temp
			bt0 = bedTemp
			tSP0 = tempSP
			btSP0 = bedTempSP
			x0 = x1 + 1

		#Draw the grid
		for x in xrange(w, 0, -30):
			dc.SetPen(bgLinePen)
			dc.DrawLine(x, 0, x, h)
		tmpNr = 0
		for y in xrange(h - 1, 0, -h * 50 / 350):
			dc.SetPen(bgLinePen)
			dc.DrawLine(0, y, w, y)
			dc.DrawText(str(tmpNr), 0, y - dc.GetFont().GetPixelSize().GetHeight())
			tmpNr += 50
		dc.DrawLine(0, 0, w, 0)
		dc.DrawLine(0, 0, 0, h)

		#Draw the main lines
		x0 = 0
		t0 = []
		bt0 = 0
		tSP0 = []
		btSP0 = 0
		for temp, tempSP, bedTemp, bedTempSP, t in self._points:
			x1 = int(w - (now - t))
			for x in xrange(x0, x1 + 1):
				for n in xrange(0, min(len(t0), len(temp))):
					t = float(x - x0) / float(x1 - x0 + 1) * (temp[n] - t0[n]) + t0[n]
					tSP = float(x - x0) / float(x1 - x0 + 1) * (tempSP[n] - tSP0[n]) + tSP0[n]
					dc.SetPen(tempSPPen)
					dc.DrawPoint(x, h - (tSP * h / 350))
					dc.SetPen(tempPen)
					dc.DrawPoint(x, h - (t * h / 350))
				bt = float(x - x0) / float(x1 - x0 + 1) * (bedTemp - bt0) + bt0
				btSP = float(x - x0) / float(x1 - x0 + 1) * (bedTempSP - btSP0) + btSP0
				dc.SetPen(bedTempSPPen)
				dc.DrawPoint(x, h - (btSP * h / 350))
				dc.SetPen(bedTempPen)
				dc.DrawPoint(x, h - (bt * h / 350))
			t0 = temp
			bt0 = bedTemp
			tSP0 = tempSP
			btSP0 = bedTempSP
			x0 = x1 + 1

		del dc
		self.Refresh(eraseBackground=False)
		self.Update()

		if len(self._points) > 0 and (time.time() - self._points[0][4]) > w + 20:
			self._points.pop(0)

	def addPoint(self, temp, tempSP, bedTemp, bedTempSP):
		if len(self._points) > 0 and time.time() - self._points[-1][4] < 0.5:
			return
		for n in xrange(0, len(temp)):
			if temp[n] is None:
				temp[n] = 0
		for n in xrange(0, len(tempSP)):
			if tempSP[n] is None:
				tempSP[n] = 0
		if bedTemp is None:
			bedTemp = 0
		if bedTempSP is None:
			bedTempSP = 0
		self._points.append((temp[:], tempSP[:], bedTemp, bedTempSP, time.time()))
		wx.CallAfter(self.UpdateDrawing)

class LogWindow(wx.Frame):
	def __init__(self, logText):
		super(LogWindow, self).__init__(None, title=_("Error log"))
		self.textBox = wx.TextCtrl(self, -1, logText, style=wx.TE_MULTILINE | wx.TE_DONTWRAP | wx.TE_READONLY)
		self.SetSize((500, 400))
		self.Show(True)
