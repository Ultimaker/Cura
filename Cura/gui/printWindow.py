__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import power
import time
import sys
import os
import ctypes

#TODO: This does not belong here!
if sys.platform.startswith('win'):
	def preventComputerFromSleeping(prevent):
		"""
		Function used to prevent the computer from going into sleep mode.
		:param prevent: True = Prevent the system from going to sleep from this point on.
		:param prevent: False = No longer prevent the system from going to sleep.
		"""
		ES_CONTINUOUS = 0x80000000
		ES_SYSTEM_REQUIRED = 0x00000001
		#SetThreadExecutionState returns 0 when failed, which is ignored. The function should be supported from windows XP and up.
		if prevent:
			ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
		else:
			ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

else:
	def preventComputerFromSleeping(prevent):
		#No preventComputerFromSleeping for MacOS and Linux yet.
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

		variables = {
			'setImage': self.script_setImage,
			'addColorCommand': self.script_addColorCommand,
			'addTerminal': self.script_addTerminal,
			'addTemperatureGraph': self.script_addTemperatureGraph,
			'addProgressbar': self.script_addProgressbar,
			'addButton': self.script_addButton,
			'addSpinner': self.script_addSpinner,

			'sendGCode': self.script_sendGCode,
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
		preventComputerFromSleeping(True)

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
		spinner = wx.SpinCtrl(self, -1, style=wx.TE_PROCESS_ENTER)
		spinner.SetRange(0, 300)
		spinner.SetPosition((x, y))
		spinner.SetSize((w, h))
		spinner.command = command
		spinner.data = data
		self._buttonList.append(spinner)
		self.Bind(wx.EVT_SPINCTRL, lambda e: command(data % (spinner.GetValue())), spinner)

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

	def script_connect(self, data = None):
		self._printerConnection.openActiveConnection()

	def script_startPrint(self, data = None):
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
			if self._printerConnection.isPrinting():
				pass #TODO: Give warning that the close will kill the print.
			self._printerConnection.closeActiveConnection()
		self._printerConnection.removeCallback(self._doPrinterConnectionUpdate)
		#TODO: When multiple printer windows are open, closing one will enable sleeping again.
		preventComputerFromSleeping(False)
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
			if e.GetKeyCode() == wx.WXK_DOWN:
				self._termHistoryIdx -= 1
				if self._termHistoryIdx >= len(self._termHistory):
					self._termHistoryIdx = 0
				self._termInput.SetValue(self._termHistory[self._termHistoryIdx])
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
		for button in self._buttonList:
			if button.command == self.script_connect:
				button.Show(self._printerConnection.hasActiveConnection())
				button.Enable(not self._printerConnection.isActiveConnectionOpen() and not self._printerConnection.isActiveConnectionOpening())
			elif button.command == self.script_pausePrint:
				button.Show(self._printerConnection.hasPause())
				if not self._printerConnection.hasActiveConnection() or self._printerConnection.isActiveConnectionOpen():
					button.Enable(self._printerConnection.isPrinting() or self._printerConnection.isPaused())
				else:
					button.Enable(False)
			elif button.command == self.script_startPrint:
				if not self._printerConnection.hasActiveConnection() or self._printerConnection.isActiveConnectionOpen():
					button.Enable(not self._printerConnection.isPrinting())
				else:
					button.Enable(False)
			elif button.command == self.script_cancelPrint:
				if not self._printerConnection.hasActiveConnection() or self._printerConnection.isActiveConnectionOpen():
					button.Enable(self._printerConnection.isPrinting())
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

		if extraInfo is not None:
			self._addTermLog('< %s\n' % (extraInfo))

		self._updateButtonStates()
		if self._progressBar is not None:
			if connection.isPrinting():
				self._progressBar.SetValue(connection.getPrintProgress() * 1000)
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
			self.SetTitle(info.replace('\n', ', '))

class printWindowBasic(wx.Frame):
	"""
	Printing window for USB printing, network printing, and any other type of printer connection we can think off.
	This is only a basic window with minimal information.
	"""
	def __init__(self, parent, printerConnection):
		super(printWindowBasic, self).__init__(parent, -1, style=wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.CAPTION|wx.SYSTEM_MENU|wx.FRAME_TOOL_WINDOW|wx.FRAME_FLOAT_ON_PARENT, title=_("Printing on %s") % (printerConnection.getName()))
		self._printerConnection = printerConnection
		self._lastUpdateTime = 0

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
		self.powerManagement = power.PowerManagement()
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
		preventComputerFromSleeping(True)

	def OnPowerWarningChange(self, e):
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
			if self._printerConnection.isPrinting():
				pass #TODO: Give warning that the close will kill the print.
			self._printerConnection.closeActiveConnection()
		self._printerConnection.removeCallback(self._doPrinterConnectionUpdate)
		#TODO: When multiple printer windows are open, closing one will enable sleeping again.
		preventComputerFromSleeping(False)
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

	def OnErrorLog(self, e):
		LogWindow(self._printerConnection.getErrorLog())

	def _doPrinterConnectionUpdate(self, connection, extraInfo = None):
		wx.CallAfter(self.__doPrinterConnectionUpdate, connection, extraInfo)
		#temp = [connection.getTemperature(0)]
		#self.temperatureGraph.addPoint(temp, [0], connection.getBedTemperature(), 0)

	def __doPrinterConnectionUpdate(self, connection, extraInfo):
		t = time.time()
		if self._lastUpdateTime + 0.5 > t and extraInfo is None:
			return
		self._lastUpdateTime = t

		if extraInfo is not None:
			self._addTermLog('< %s\n' % (extraInfo))

		self._updateButtonStates()
		if connection.isPrinting():
			self.progress.SetValue(connection.getPrintProgress() * 1000)
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

	def _updateButtonStates(self):
		self.connectButton.Show(self._printerConnection.hasActiveConnection())
		self.connectButton.Enable(not self._printerConnection.isActiveConnectionOpen() and not self._printerConnection.isActiveConnectionOpening())
		self.pauseButton.Show(self._printerConnection.hasPause())
		if not self._printerConnection.hasActiveConnection() or self._printerConnection.isActiveConnectionOpen():
			self.printButton.Enable(not self._printerConnection.isPrinting())
			self.pauseButton.Enable(self._printerConnection.isPrinting())
			self.cancelButton.Enable(self._printerConnection.isPrinting())
		else:
			self.printButton.Enable(False)
			self.pauseButton.Enable(False)
			self.cancelButton.Enable(False)
		self.errorLogButton.Show(self._printerConnection.isInErrorState())

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
					dc.DrawLine(x, h, x, h - (t * h / 300))
				bt = float(x - x0) / float(x1 - x0 + 1) * (bedTemp - bt0) + bt0
				dc.SetPen(bedTempPenBG)
				dc.DrawLine(x, h, x, h - (bt * h / 300))
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
		for y in xrange(h - 1, 0, -h * 50 / 300):
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
					dc.DrawPoint(x, h - (tSP * h / 300))
					dc.SetPen(tempPen)
					dc.DrawPoint(x, h - (t * h / 300))
				bt = float(x - x0) / float(x1 - x0 + 1) * (bedTemp - bt0) + bt0
				btSP = float(x - x0) / float(x1 - x0 + 1) * (bedTempSP - btSP0) + btSP0
				dc.SetPen(bedTempSPPen)
				dc.DrawPoint(x, h - (btSP * h / 300))
				dc.SetPen(bedTempPen)
				dc.DrawPoint(x, h - (bt * h / 300))
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
		super(LogWindow, self).__init__(None, title="Error log")
		self.textBox = wx.TextCtrl(self, -1, logText, style=wx.TE_MULTILINE | wx.TE_DONTWRAP | wx.TE_READONLY)
		self.SetSize((500, 400))
		self.Show(True)
