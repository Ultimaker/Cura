__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import power
import time

from wx.lib import buttons

from Cura.util import profile
from Cura.util import resources

class printWindow(wx.Frame):
	"Main user interface window"

	def __init__(self, printerConnection):
		super(printWindow, self).__init__(None, -1, title=_("Printing"))
		self._printerConnection = printerConnection
		self.lastUpdateTime = 0

		self.SetSizer(wx.BoxSizer())
		self.panel = wx.Panel(self)
		self.GetSizer().Add(self.panel, 1, flag=wx.EXPAND)
		self.sizer = wx.GridBagSizer(2, 2)
		self.panel.SetSizer(self.sizer)

		sb = wx.StaticBox(self.panel, label=_("Statistics"))
		boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.powerWarningText = wx.StaticText(parent=self.panel,
			id=-1,
			label=_("Your computer is running on battery power.\nConnect your computer to AC power or your print might not finish."),
			style=wx.ALIGN_CENTER)
		self.powerWarningText.SetBackgroundColour('red')
		self.powerWarningText.SetForegroundColour('white')
		boxsizer.AddF(self.powerWarningText, flags=wx.SizerFlags().Expand().Border(wx.BOTTOM, 10))
		self.powerManagement = power.PowerManagement()
		self.powerWarningTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnPowerWarningChange, self.powerWarningTimer)
		self.OnPowerWarningChange(None)
		self.powerWarningTimer.Start(10000)

		self.statsText = wx.StaticText(self.panel, -1, _("Filament: ####.##m #.##g\nEstimated print time: #####:##\nMachine state:\nDetecting baudrateXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"))
		boxsizer.Add(self.statsText, flag=wx.LEFT, border=5)

		self.sizer.Add(boxsizer, pos=(0, 0), span=(7, 1), flag=wx.EXPAND)

		self.connectButton = wx.Button(self.panel, -1, _("Connect"))
		#self.loadButton = wx.Button(self.panel, -1, 'Load')
		self.printButton = wx.Button(self.panel, -1, _("Print"))
		self.pauseButton = wx.Button(self.panel, -1, _("Pause"))
		self.cancelButton = wx.Button(self.panel, -1, _("Cancel print"))
		self.errorLogButton = wx.Button(self.panel, -1, _("Error log"))
		self.progress = wx.Gauge(self.panel, -1, range=1000)

		self.sizer.Add(self.connectButton, pos=(1, 1), flag=wx.EXPAND)
		#self.sizer.Add(self.loadButton, pos=(1,1), flag=wx.EXPAND)
		self.sizer.Add(self.printButton, pos=(2, 1), flag=wx.EXPAND)
		self.sizer.Add(self.pauseButton, pos=(3, 1), flag=wx.EXPAND)
		self.sizer.Add(self.cancelButton, pos=(4, 1), flag=wx.EXPAND)
		self.sizer.Add(self.errorLogButton, pos=(5, 1), flag=wx.EXPAND)
		self.sizer.Add(self.progress, pos=(7, 0), span=(1, 7), flag=wx.EXPAND)

		nb = wx.Notebook(self.panel)
		self.tabs = nb
		self.sizer.Add(nb, pos=(0, 2), span=(7, 4), flag=wx.EXPAND)

		self.temperaturePanel = wx.Panel(nb)
		sizer = wx.GridBagSizer(2, 2)
		self.temperaturePanel.SetSizer(sizer)

		self.temperatureSelect = wx.SpinCtrl(self.temperaturePanel, -1, '0', size=(21 * 3, 21), style=wx.SP_ARROW_KEYS)
		self.temperatureSelect.SetRange(0, 400)
		self.temperatureHeatUp = wx.Button(self.temperaturePanel, -1, str(int(profile.getProfileSettingFloat('print_temperature'))) + 'C')
		self.bedTemperatureLabel = wx.StaticText(self.temperaturePanel, -1, _("BedTemp:"))
		self.bedTemperatureSelect = wx.SpinCtrl(self.temperaturePanel, -1, '0', size=(21 * 3, 21), style=wx.SP_ARROW_KEYS)
		self.bedTemperatureSelect.SetRange(0, 400)
		self.bedTemperatureLabel.Show(False)
		self.bedTemperatureSelect.Show(False)

		self.temperatureGraph = TemperatureGraph(self.temperaturePanel)

		sizer.Add(wx.StaticText(self.temperaturePanel, -1, _("Temp:")), pos=(0, 0))
		sizer.Add(self.temperatureSelect, pos=(0, 1))
		sizer.Add(self.temperatureHeatUp, pos=(0, 2))
		sizer.Add(self.bedTemperatureLabel, pos=(1, 0))
		sizer.Add(self.bedTemperatureSelect, pos=(1, 1))
		sizer.Add(self.temperatureGraph, pos=(2, 0), span=(1, 3), flag=wx.EXPAND)
		sizer.AddGrowableRow(2)
		sizer.AddGrowableCol(2)

		nb.AddPage(self.temperaturePanel, 'Temp')

		self.directControlPanel = wx.Panel(nb)

		sizer = wx.GridBagSizer(2, 2)
		self.directControlPanel.SetSizer(sizer)
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Y100 F6000', 'G90'], 'print-move-y100.png'), pos=(0, 3))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Y10 F6000', 'G90'], 'print-move-y10.png'), pos=(1, 3))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Y1 F6000', 'G90'], 'print-move-y1.png'), pos=(2, 3))

		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Y-1 F6000', 'G90'], 'print-move-y-1.png'), pos=(4, 3))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Y-10 F6000', 'G90'], 'print-move-y-10.png'), pos=(5, 3))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Y-100 F6000', 'G90'], 'print-move-y-100.png'), pos=(6, 3))

		sizer.Add(PrintCommandButton(self, ['G91', 'G1 X-100 F6000', 'G90'], 'print-move-x-100.png'), pos=(3, 0))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 X-10 F6000', 'G90'], 'print-move-x-10.png'), pos=(3, 1))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 X-1 F6000', 'G90'], 'print-move-x-1.png'), pos=(3, 2))

		sizer.Add(PrintCommandButton(self, ['G28 X0 Y0'], 'print-move-home.png'), pos=(3, 3))

		sizer.Add(PrintCommandButton(self, ['G91', 'G1 X1 F6000', 'G90'], 'print-move-x1.png'), pos=(3, 4))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 X10 F6000', 'G90'], 'print-move-x10.png'), pos=(3, 5))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 X100 F6000', 'G90'], 'print-move-x100.png'), pos=(3, 6))

		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Z10 F200', 'G90'], 'print-move-z10.png'), pos=(0, 8))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Z1 F200', 'G90'], 'print-move-z1.png'), pos=(1, 8))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Z0.1 F200', 'G90'], 'print-move-z0.1.png'), pos=(2, 8))

		sizer.Add(PrintCommandButton(self, ['G28 Z0'], 'print-move-home.png'), pos=(3, 8))

		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Z-0.1 F200', 'G90'], 'print-move-z-0.1.png'), pos=(4, 8))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Z-1 F200', 'G90'], 'print-move-z-1.png'), pos=(5, 8))
		sizer.Add(PrintCommandButton(self, ['G91', 'G1 Z-10 F200', 'G90'], 'print-move-z-10.png'), pos=(6, 8))

		sizer.Add(PrintCommandButton(self, ['G92 E0', 'G1 E2 F120'], 'extrude.png', size=(60, 20)), pos=(1, 10), span=(1, 3), flag=wx.EXPAND)
		sizer.Add(PrintCommandButton(self, ['G92 E0', 'G1 E-2 F120'], 'retract.png', size=(60, 20)), pos=(2, 10), span=(1, 3), flag=wx.EXPAND)

		nb.AddPage(self.directControlPanel, _("Jog"))

		self.termPanel = wx.Panel(nb)
		sizer = wx.GridBagSizer(2, 2)
		self.termPanel.SetSizer(sizer)

		f = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False)
		self.termLog = wx.TextCtrl(self.termPanel, style=wx.TE_MULTILINE | wx.TE_DONTWRAP)
		self.termLog.SetFont(f)
		self.termLog.SetEditable(0)
		self.termInput = wx.TextCtrl(self.termPanel, style=wx.TE_PROCESS_ENTER)
		self.termInput.SetFont(f)
		self._termHistory = []
		self._termHistoryIdx = 0

		sizer.Add(self.termLog, pos=(0, 0), flag=wx.EXPAND)
		sizer.Add(self.termInput, pos=(1, 0), flag=wx.EXPAND)
		sizer.AddGrowableCol(0)
		sizer.AddGrowableRow(0)

		nb.AddPage(self.termPanel, _("Term"))

		self.sizer.AddGrowableRow(6)
		self.sizer.AddGrowableCol(3)

		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.connectButton.Bind(wx.EVT_BUTTON, self.OnConnect)
		#self.loadButton.Bind(wx.EVT_BUTTON, self.OnLoad)
		self.printButton.Bind(wx.EVT_BUTTON, self.OnPrint)
		self.pauseButton.Bind(wx.EVT_BUTTON, self.OnPause)
		self.cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)
		self.errorLogButton.Bind(wx.EVT_BUTTON, self.OnErrorLog)

		self.Bind(wx.EVT_BUTTON, lambda e: (self.temperatureSelect.SetValue(int(profile.getProfileSettingFloat('print_temperature'))), self.machineCom.sendCommand("M104 S%d" % (int(profile.getProfileSettingFloat('print_temperature'))))), self.temperatureHeatUp)
		self.Bind(wx.EVT_SPINCTRL, self.OnTempChange, self.temperatureSelect)
		self.Bind(wx.EVT_SPINCTRL, self.OnBedTempChange, self.bedTemperatureSelect)

		self.Bind(wx.EVT_TEXT_ENTER, self.OnTermEnterLine, self.termInput)
		self.termInput.Bind(wx.EVT_CHAR, self.OnTermKey)

		self.Layout()
		self.Fit()
		self.Centre()

		self.statsText.SetMinSize(self.statsText.GetSize())
		self.statsText.SetLabel(self._printerConnection.getStatusString())

		self.UpdateButtonStates()

		self._printerConnection.addCallback(self._doPrinterConnectionUpdate)

	def OnPowerWarningChange(self, e):
		type = self.powerManagement.get_providing_power_source_type()
		if type == power.POWER_TYPE_AC and self.powerWarningText.IsShown():
			self.powerWarningText.Hide()
			self.panel.Layout()
			self.Layout()
		elif type != power.POWER_TYPE_AC and not self.powerWarningText.IsShown():
			self.powerWarningText.Show()
			self.panel.Layout()
			self.Layout()

	def OnClose(self, e):
		self._printerConnection.closeActiveConnection()
		self._printerConnection.removeCallback(self._doPrinterConnectionUpdate)
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

	def OnTempChange(self, e):
		if not self._printerConnection.isAbleToSendDirectCommand():
			return
		self._printerConnection.sendCommand("M104 S%d" % (self.temperatureSelect.GetValue()))

	def OnBedTempChange(self, e):
		if not self._printerConnection.isAbleToSendDirectCommand():
			return
		self._printerConnection.sendCommand("M140 S%d" % (self.bedTemperatureSelect.GetValue()))

	def OnTermEnterLine(self, e):
		if not self._printerConnection.isAbleToSendDirectCommand():
			return
		line = self.termInput.GetValue()
		if line == '':
			return
		self._addTermLog('>%s\n' % (line))
		self._printerConnection.sendCommand(line)
		self._termHistory.append(line)
		self._termHistoryIdx = len(self._termHistory)
		self.termInput.SetValue('')

	def OnTermKey(self, e):
		if len(self._termHistory) > 0:
			if e.GetKeyCode() == wx.WXK_UP:
				self._termHistoryIdx -= 1
				if self._termHistoryIdx < 0:
					self._termHistoryIdx = len(self._termHistory) - 1
				self.termInput.SetValue(self._termHistory[self._termHistoryIdx])
			if e.GetKeyCode() == wx.WXK_DOWN:
				self._termHistoryIdx -= 1
				if self._termHistoryIdx >= len(self._termHistory):
					self._termHistoryIdx = 0
				self.termInput.SetValue(self._termHistory[self._termHistoryIdx])
		e.Skip()

	def _addTermLog(self, line):
		if len(self.termLog.GetValue()) > 10000:
			self.termLog.SetValue(self.termLog.GetValue()[-10000:])
		self.termLog.SetInsertionPointEnd()
		self.termLog.AppendText(line.encode('utf-8', 'replace'))

	def _doPrinterConnectionUpdate(self, connection, extraInfo = None):
		wx.CallAfter(self.__doPrinterConnectionUpdate, connection, extraInfo)
		temp = [connection.getTemperature(0)]
		self.temperatureGraph.addPoint(temp, [0], connection.getBedTemperature(), 0)

	def __doPrinterConnectionUpdate(self, connection, extraInfo):
		t = time.time()
		if self.lastUpdateTime + 0.5 > t:
			return
		self.lastUpdateTime = t

		self.UpdateButtonStates()
		if connection.isPrinting():
			self.progress.SetValue(connection.getPrintProgress() * 1000)
		else:
			self.progress.SetValue(0)
		self.statsText.SetLabel(connection.getStatusString())

	def UpdateButtonStates(self):
		self.connectButton.Show(self._printerConnection.hasActiveConnection())
		self.connectButton.Enable(not self._printerConnection.isActiveConnectionOpen())
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

		self.directControlPanel.Enable(self._printerConnection.isAbleToSendDirectCommand())
		self.temperatureSelect.Enable(self._printerConnection.isAbleToSendDirectCommand())
		self.temperatureHeatUp.Enable(self._printerConnection.isAbleToSendDirectCommand())
		self.termInput.Enable(self._printerConnection.isAbleToSendDirectCommand())

class PrintCommandButton(buttons.GenBitmapButton):
	def __init__(self, parent, commandList, bitmapFilename, size=(20, 20)):
		self.bitmap = wx.Bitmap(resources.getPathForImage(bitmapFilename))
		super(PrintCommandButton, self).__init__(parent.directControlPanel, -1, self.bitmap, size=size)

		self.commandList = commandList
		self.parent = parent

		self.SetBezelWidth(1)
		self.SetUseFocusIndicator(False)

		self.Bind(wx.EVT_BUTTON, self.OnClick)

	def OnClick(self, e):
		if self.parent._printerConnection is None or self.parent._printerConnection.isAbleToSendDirectCommand():
			return
		for cmd in self.commandList:
			self.parent._printerConnection.sendCommand(cmd)
		e.Skip()

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
		self.SetMinSize((320, 200))

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
		t0 = [0] * len(self._points[0][0])
		bt0 = 0
		tSP0 = 0
		btSP0 = 0
		for temp, tempSP, bedTemp, bedTempSP, t in self._points:
			x1 = int(w - (now - t))
			for x in xrange(x0, x1 + 1):
				for n in xrange(0, len(temp)):
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
		t0 = [0] * len(self._points[0][0])
		bt0 = 0
		tSP0 = [0] * len(self._points[0][0])
		btSP0 = 0
		for temp, tempSP, bedTemp, bedTempSP, t in self._points:
			x1 = int(w - (now - t))
			for x in xrange(x0, x1 + 1):
				for n in xrange(0, len(temp)):
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
		self.Centre()
		self.Show(True)
