__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import time

from Cura.util import machineCom

class debuggerWindow(wx.Frame):
	def __init__(self, parent):
		super(debuggerWindow, self).__init__(parent, title='Cura - PID Debugger')

		self.machineCom = None
		self.machineCom = machineCom.MachineCom(callbackObject=self)
		self.coolButton = wx.Button(self, -1, '0C')
		self.heatupButton = wx.Button(self, -1, '200C')
		self.heatupButton2 = wx.Button(self, -1, '260C')
		self.heatupButton3 = wx.Button(self, -1, '300C')
		self.fanOn = wx.Button(self, -1, 'Fan ON')
		self.fanOn50 = wx.Button(self, -1, 'Fan ON 50%')
		self.fanOff = wx.Button(self, -1, 'Fan OFF')
		self.graph = temperatureGraph(self)
		self.targetTemp = 0
		self.pValue = wx.TextCtrl(self, -1, '0')
		self.iValue = wx.TextCtrl(self, -1, '0')
		self.dValue = wx.TextCtrl(self, -1, '0')

		self.sizer = wx.GridBagSizer(0, 0)
		self.SetSizer(self.sizer)
		self.sizer.Add(self.graph, pos=(0, 0), span=(1, 8), flag=wx.EXPAND)
		self.sizer.Add(self.coolButton, pos=(1, 0), flag=wx.EXPAND)
		self.sizer.Add(self.heatupButton, pos=(1, 1), flag=wx.EXPAND)
		self.sizer.Add(self.heatupButton2, pos=(1, 2), flag=wx.EXPAND)
		self.sizer.Add(self.heatupButton3, pos=(1, 3), flag=wx.EXPAND)
		self.sizer.Add(self.fanOn, pos=(1, 4), flag=wx.EXPAND)
		self.sizer.Add(self.fanOn50, pos=(1, 5), flag=wx.EXPAND)
		self.sizer.Add(self.fanOff, pos=(1, 6), flag=wx.EXPAND)
		self.sizer.Add(self.pValue, pos=(2, 0), flag=wx.EXPAND)
		self.sizer.Add(self.iValue, pos=(2, 1), flag=wx.EXPAND)
		self.sizer.Add(self.dValue, pos=(2, 2), flag=wx.EXPAND)
		self.sizer.AddGrowableCol(7)
		self.sizer.AddGrowableRow(0)

		wx.EVT_CLOSE(self, self.OnClose)
		self.Bind(wx.EVT_BUTTON, lambda e: self.setTemp(0), self.coolButton)
		self.Bind(wx.EVT_BUTTON, lambda e: self.setTemp(200), self.heatupButton)
		self.Bind(wx.EVT_BUTTON, lambda e: self.setTemp(260), self.heatupButton2)
		self.Bind(wx.EVT_BUTTON, lambda e: self.setTemp(300), self.heatupButton3)
		self.Bind(wx.EVT_BUTTON, lambda e: self.machineCom.sendCommand('M106'), self.fanOn)
		self.Bind(wx.EVT_BUTTON, lambda e: self.machineCom.sendCommand('M106 S128'), self.fanOn50)
		self.Bind(wx.EVT_BUTTON, lambda e: self.machineCom.sendCommand('M107'), self.fanOff)
		self.Bind(wx.EVT_TEXT, self.updatePID, self.pValue)
		self.Bind(wx.EVT_TEXT, self.updatePID, self.iValue)
		self.Bind(wx.EVT_TEXT, self.updatePID, self.dValue)

		self.Layout()
		self.Fit()

	def updatePID(self, e):
		try:
			p = float(self.pValue.GetValue())
			i = float(self.iValue.GetValue())
			d = float(self.dValue.GetValue())
		except:
			return
		self.machineCom.sendCommand("M301 P%f I%f D%f" % (p, i, d))

	def setTemp(self, temp):
		self.targetTemp = temp
		self.machineCom.sendCommand("M104 S%d" % (temp))

	def OnClose(self, e):
		self.machineCom.close()
		self.Destroy()

	def mcLog(self, message):
		pass

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		pass

	def mcStateChange(self, state):
		if self.machineCom is not None and self.machineCom.isOperational():
			self.machineCom.sendCommand("M503\n")
			self.machineCom.sendCommand("M503\n")

	def mcMessage(self, message):
		if 'PIDDEBUG' in message:
			#echo: PIDDEBUG 0: Input 40.31 Output 0.00 pTerm 0.00 iTerm 0.00 dTerm 0.00
			message = message.strip().split()
			temperature = float(message[message.index("Input")+1])
			heater_output = float(message[message.index("Output")+1])
			pTerm = float(message[message.index("pTerm")+1])
			iTerm = float(message[message.index("iTerm")+1])
			dTerm = float(message[message.index("dTerm")+1])

			self.graph.addPoint(temperature, heater_output, pTerm, iTerm, dTerm, self.targetTemp)
		elif 'M301' in message:
			for m in message.strip().split():
				if m[0] == 'P':
					wx.CallAfter(self.pValue.SetValue, m[1:])
				if m[0] == 'I':
					wx.CallAfter(self.iValue.SetValue, m[1:])
				if m[0] == 'D':
					wx.CallAfter(self.dValue.SetValue, m[1:])

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass

class temperatureGraph(wx.Panel):
	def __init__(self, parent):
		super(temperatureGraph, self).__init__(parent)

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_PAINT, self.OnDraw)

		self.lastDraw = time.time() - 1.0
		self.points = []
		self.backBuffer = None
		self.SetMinSize((320, 200))
		self.addPoint(0,0,0,0,0,0)

	def OnEraseBackground(self, e):
		pass

	def OnSize(self, e):
		if self.backBuffer is None or self.GetSize() != self.backBuffer.GetSize():
			self.backBuffer = wx.EmptyBitmap(*self.GetSizeTuple())
			self.UpdateDrawing(True)

	def OnDraw(self, e):
		dc = wx.BufferedPaintDC(self, self.backBuffer)

	def _drawBackgroundForLine(self, dc, color, f):
		w, h = self.GetSizeTuple()
		color = wx.Pen(color)
		dc.SetPen(color)
		x0 = 0
		v0 = 0
		for p in self.points:
			x1 = int(w - (self.now - p[0]) * self.timeScale)
			value = f(p)
			for x in xrange(x0, x1 + 1):
				v = float(x - x0) / float(x1 - x0 + 1) * (value - v0) + v0
				dc.DrawLine(x, h, x, h - (v * h / 300))
			v0 = value
			x0 = x1 + 1

	def _drawLine(self, dc, color, f):
		w, h = self.GetSizeTuple()
		color = wx.Pen(color)
		dc.SetPen(color)
		x0 = 0
		v0 = 0
		for p in self.points:
			x1 = int(w - (self.now - p[0]) * self.timeScale)
			value = f(p)
			dc.DrawLine(x0, h - (v0 * h / 300), x1, h - (value * h / 300), )
			dc.DrawPoint(x1, h - (value * h / 300), )
			v0 = value
			x0 = x1 + 1

	def UpdateDrawing(self, force=False):
		now = time.time()
		self.timeScale = 10
		self.now = now
		if not force and now - self.lastDraw < 0.1:
			return
		self.lastDraw = now
		dc = wx.MemoryDC()
		dc.SelectObject(self.backBuffer)
		dc.Clear()
		dc.SetFont(wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT))
		w, h = self.GetSizeTuple()
		bgLinePen = wx.Pen('#A0A0A0')

		#Draw the background up to the current temperatures.
		self._drawBackgroundForLine(dc, '#FFD0D0', lambda p: p[1])#temp
		self._drawBackgroundForLine(dc, '#D0D0FF', lambda p: p[3])#pTerm
		self._drawBackgroundForLine(dc, '#D0FFD0', lambda p: abs(p[5]))#dTerm

		#Draw the grid
		for x in xrange(w, 0, -5 * self.timeScale):
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
		if len(self.points) > 10:
			tempAvg = 0.0
			heaterAvg = 0.0
			for n in xrange(0, 10):
				tempAvg += self.points[-n-1][1]
				heaterAvg += self.points[-n-1][2]
			dc.DrawText("Temp: %d Heater: %d" % (tempAvg / 10, heaterAvg * 100 / 255 / 10), 0, 0)

		#Draw the main lines
		self._drawLine(dc, '#404040', lambda p: p[6])#target
		self._drawLine(dc, '#40FFFF', lambda p: p[3])#pTerm
		self._drawLine(dc, '#FF40FF', lambda p: p[4])#iTerm
		self._drawLine(dc, '#FFFF40', lambda p: p[5])#dTerm
		self._drawLine(dc, '#4040FF', lambda p: -p[5])#dTerm
		self._drawLine(dc, '#FF4040', lambda p: p[1])#temp
		self._drawLine(dc, '#40FF40', lambda p: p[2])#heater

		del dc
		self.Refresh(eraseBackground=False)
		self.Update()

		if len(self.points) > 0 and (time.time() - self.points[0][0]) > (w + 20) / self.timeScale:
			self.points.pop(0)

	def addPoint(self, temperature, heater_output, pTerm, iTerm, dTerm, targetTemp):
		self.points.append([time.time(), temperature, heater_output, pTerm, iTerm, dTerm, targetTemp])
		wx.CallAfter(self.UpdateDrawing)
