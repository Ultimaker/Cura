from __future__ import absolute_import
from __future__ import division

import math
import threading
import re
import time
import os
import numpy

from wx import glcanvas
import wx
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.util import profile
from Cura.util import gcodeInterpreter
from Cura.util import meshLoader
from Cura.util import util3d
from Cura.util import sliceRun

from Cura.gui.util import opengl
from Cura.gui.util import previewTools
from Cura.gui.util import openglGui

class previewObject():
	def __init__(self):
		self.mesh = None
		self.filename = None
		self.displayList = None
		self.dirty = False

class previewPanel(wx.Panel):
	def __init__(self, parent):
		super(previewPanel, self).__init__(parent,-1)
		
		self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DDKSHADOW))
		self.SetMinSize((440,320))

		self.objectList = []
		self.errorList = []
		self.gcode = None
		self.objectsMinV = None
		self.objectsMaxV = None
		self.objectsBoundaryCircleSize = None
		self.loadThread = None
		self.machineSize = util3d.Vector3(profile.getPreferenceFloat('machine_width'), profile.getPreferenceFloat('machine_depth'), profile.getPreferenceFloat('machine_height'))
		self.machineCenter = util3d.Vector3(self.machineSize.x / 2, self.machineSize.y / 2, 0)

		self.glCanvas = PreviewGLCanvas(self)
		#Create the popup window
		self.warningPopup = wx.PopupWindow(self, flags=wx.BORDER_SIMPLE)
		self.warningPopup.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INFOBK))
		self.warningPopup.text = wx.StaticText(self.warningPopup, -1, 'Reset scale, rotation and mirror?')
		self.warningPopup.yesButton = wx.Button(self.warningPopup, -1, 'yes', style=wx.BU_EXACTFIT)
		self.warningPopup.noButton = wx.Button(self.warningPopup, -1, 'no', style=wx.BU_EXACTFIT)
		self.warningPopup.sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.warningPopup.SetSizer(self.warningPopup.sizer)
		self.warningPopup.sizer.Add(self.warningPopup.text, 1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=1)
		self.warningPopup.sizer.Add(self.warningPopup.yesButton, 0, flag=wx.EXPAND|wx.ALL, border=1)
		self.warningPopup.sizer.Add(self.warningPopup.noButton, 0, flag=wx.EXPAND|wx.ALL, border=1)
		self.warningPopup.Fit()
		self.warningPopup.Layout()
		self.warningPopup.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnHideWarning, self.warningPopup.timer)
		
		self.Bind(wx.EVT_BUTTON, self.OnWarningPopup, self.warningPopup.yesButton)
		self.Bind(wx.EVT_BUTTON, self.OnHideWarning, self.warningPopup.noButton)
		parent.Bind(wx.EVT_MOVE, self.OnMove)
		parent.Bind(wx.EVT_SIZE, self.OnMove)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.glCanvas, 1, flag=wx.EXPAND)
		self.SetSizer(sizer)
		
		self.checkReloadFileTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnCheckReloadFile, self.checkReloadFileTimer)
		self.checkReloadFileTimer.Start(1000)

		group = []
		self.rotateToolButton = openglGui.glRadioButton(self.glCanvas, 8, 'Rotate', (0,-1), group, self.OnToolSelect)
		self.scaleToolButton  = openglGui.glRadioButton(self.glCanvas, 9, 'Scale', (1,-1), group, self.OnToolSelect)
		self.mirrorToolButton  = openglGui.glRadioButton(self.glCanvas, 10, 'Mirror', (2,-1), group, self.OnToolSelect)

		self.resetRotationButton = openglGui.glButton(self.glCanvas, 12, 'Reset', (0,-2), self.OnRotateReset)
		self.layFlatButton       = openglGui.glButton(self.glCanvas, 16, 'Lay flat', (0,-3), self.OnLayFlat)

		self.resetScaleButton    = openglGui.glButton(self.glCanvas, 13, 'Reset', (1,-2), self.OnScaleReset)
		self.scaleMaxButton      = openglGui.glButton(self.glCanvas, 17, 'To max', (1,-3), self.OnScaleMax)

		self.mirrorXButton       = openglGui.glButton(self.glCanvas, 14, 'Mirror X', (2,-2), lambda : self.OnMirror(0))
		self.mirrorYButton       = openglGui.glButton(self.glCanvas, 18, 'Mirror Y', (2,-3), lambda : self.OnMirror(1))
		self.mirrorZButton       = openglGui.glButton(self.glCanvas, 22, 'Mirror Z', (2,-4), lambda : self.OnMirror(2))

		self.openFileButton      = openglGui.glButton(self.glCanvas, 4, 'Load', (0,0), lambda : self.GetParent().GetParent().GetParent()._showModelLoadDialog(1))
		self.sliceButton         = openglGui.glButton(self.glCanvas, 5, 'Prepare', (1,0), lambda : self.GetParent().GetParent().GetParent().OnSlice(None))
		self.printButton         = openglGui.glButton(self.glCanvas, 6, 'Print', (2,0), lambda : self.GetParent().GetParent().GetParent().OnPrint(None))

		self.rotateToolButton.setExpandArrow(True)
		self.scaleToolButton.setExpandArrow(True)
		self.mirrorToolButton.setExpandArrow(True)

		extruderCount = int(profile.getPreference('extruder_amount'))
		if extruderCount > 1:
			openglGui.glButton(self.glCanvas, 4, 'Load dual', (0,1), lambda : self.GetParent().GetParent().GetParent()._showModelLoadDialog(2))
		if extruderCount > 2:
			openglGui.glButton(self.glCanvas, 4, 'Load triple', (0,2), lambda : self.GetParent().GetParent().GetParent()._showModelLoadDialog(3))
		if extruderCount > 3:
			openglGui.glButton(self.glCanvas, 4, 'Load quad', (0,3), lambda : self.GetParent().GetParent().GetParent()._showModelLoadDialog(4))

		self.scaleForm = openglGui.glFrame(self.glCanvas, (2, -2))
		openglGui.glGuiLayoutGrid(self.scaleForm)
		openglGui.glLabel(self.scaleForm, 'Scale X', (0,0))
		self.scaleXctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,0), lambda value: self.OnScaleEntry(value, 0))
		openglGui.glLabel(self.scaleForm, 'Scale Y', (0,1))
		self.scaleYctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,1), lambda value: self.OnScaleEntry(value, 1))
		openglGui.glLabel(self.scaleForm, 'Scale Z', (0,2))
		self.scaleZctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,2), lambda value: self.OnScaleEntry(value, 2))
		openglGui.glLabel(self.scaleForm, 'Size X (mm)', (0,4))
		self.scaleXmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,4), lambda value: self.OnScaleEntryMM(value, 0))
		openglGui.glLabel(self.scaleForm, 'Size Y (mm)', (0,5))
		self.scaleYmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,5), lambda value: self.OnScaleEntryMM(value, 1))
		openglGui.glLabel(self.scaleForm, 'Size Z (mm)', (0,6))
		self.scaleZmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,6), lambda value: self.OnScaleEntryMM(value, 2))
		openglGui.glLabel(self.scaleForm, 'Uniform scale', (0,8))
		self.scaleUniform = openglGui.glCheckbox(self.scaleForm, True, (1,8), None)

		self.viewSelection = openglGui.glComboButton(self.glCanvas, 'View mode', [7,11,15,19,23], ['Normal', 'Transparent', 'X-Ray', 'Overhang', 'Layers'], (-1,0), self.OnViewChange)
		self.layerSelect = openglGui.glSlider(self.glCanvas, 0, 0, 100, (-1,-2), lambda : self.Refresh())

		self.OnViewChange()
		self.OnToolSelect()
		self.updateModelTransform()

		self.matrix = numpy.matrix(numpy.array(profile.getObjectMatrix(), numpy.float64).reshape((3,3,)))

	def OnToolSelect(self):
		if self.rotateToolButton.getSelected():
			self.tool = previewTools.toolRotate(self.glCanvas)
		elif self.scaleToolButton.getSelected():
			self.tool = previewTools.toolScale(self.glCanvas)
		elif self.mirrorToolButton.getSelected():
			self.tool = previewTools.toolNone(self.glCanvas)
		else:
			self.tool = previewTools.toolNone(self.glCanvas)
		self.resetRotationButton.setHidden(not self.rotateToolButton.getSelected())
		self.layFlatButton.setHidden(not self.rotateToolButton.getSelected())
		self.resetScaleButton.setHidden(not self.scaleToolButton.getSelected())
		self.scaleMaxButton.setHidden(not self.scaleToolButton.getSelected())
		self.scaleForm.setHidden(not self.scaleToolButton.getSelected())
		self.mirrorXButton.setHidden(not self.mirrorToolButton.getSelected())
		self.mirrorYButton.setHidden(not self.mirrorToolButton.getSelected())
		self.mirrorZButton.setHidden(not self.mirrorToolButton.getSelected())
		self.updateModelTransform()

	def OnScaleEntry(self, value, axis):
		try:
			value = float(value)
		except:
			return
		scale = numpy.linalg.norm(self.matrix[::,axis].getA().flatten())
		scale = value / scale
		if scale == 0:
			return
		if self.scaleUniform.getValue():
			matrix = [[scale,0,0], [0, scale, 0], [0, 0, scale]]
		else:
			matrix = [[1.0,0,0], [0, 1.0, 0], [0, 0, 1.0]]
			matrix[axis][axis] = scale
		self.matrix *= numpy.matrix(matrix, numpy.float64)
		self.updateModelTransform()

	def OnScaleEntryMM(self, value, axis):
		try:
			value = float(value)
		except:
			return
		scale = self.objectsSize[axis]
		scale = value / scale
		if scale == 0:
			return
		if self.scaleUniform.getValue():
			matrix = [[scale,0,0], [0, scale, 0], [0, 0, scale]]
		else:
			matrix = [[1,0,0], [0, 1, 0], [0, 0, 1]]
			matrix[axis][axis] = scale
		self.matrix *= numpy.matrix(matrix, numpy.float64)
		self.updateModelTransform()

	def OnMirror(self, axis):
		matrix = [[1,0,0], [0, 1, 0], [0, 0, 1]]
		matrix[axis][axis] = -1
		self.matrix *= numpy.matrix(matrix, numpy.float64)
		for obj in self.objectList:
			obj.dirty = True
			obj.steepDirty = True
		self.updateModelTransform()

	def OnMove(self, e = None):
		if e is not None:
			e.Skip()
		x, y = self.glCanvas.ClientToScreenXY(0, 0)
		sx, sy = self.glCanvas.GetClientSizeTuple()
		self.warningPopup.SetPosition((x, y+sy-self.warningPopup.GetSize().height))

	def OnScaleMax(self):
		if self.objectsMinV is None:
			return
		vMin = self.objectsMinV
		vMax = self.objectsMaxV
		skirtSize = 3
		if profile.getProfileSettingFloat('skirt_line_count') > 0:
			skirtSize = 3 + profile.getProfileSettingFloat('skirt_line_count') * profile.calculateEdgeWidth() + profile.getProfileSettingFloat('skirt_gap')
		scaleX1 = (self.machineSize.x - self.machineCenter.x - skirtSize) / ((vMax[0] - vMin[0]) / 2)
		scaleY1 = (self.machineSize.y - self.machineCenter.y - skirtSize) / ((vMax[1] - vMin[1]) / 2)
		scaleX2 = (self.machineCenter.x - skirtSize) / ((vMax[0] - vMin[0]) / 2)
		scaleY2 = (self.machineCenter.y - skirtSize) / ((vMax[1] - vMin[1]) / 2)
		scaleZ = self.machineSize.z / (vMax[2] - vMin[2])
		scale = min(scaleX1, scaleY1, scaleX2, scaleY2, scaleZ)
		self.matrix *= numpy.matrix([[scale,0,0],[0,scale,0],[0,0,scale]], numpy.float64)
		if self.glCanvas.viewMode == 'GCode' or self.glCanvas.viewMode == 'Mixed':
			self.setViewMode('Normal')
		self.updateModelTransform()

	def OnRotateReset(self):
		x = numpy.linalg.norm(self.matrix[::,0].getA().flatten())
		y = numpy.linalg.norm(self.matrix[::,1].getA().flatten())
		z = numpy.linalg.norm(self.matrix[::,2].getA().flatten())
		self.matrix = numpy.matrix([[x,0,0],[0,y,0],[0,0,z]], numpy.float64)
		for obj in self.objectList:
			obj.dirty = True
			obj.steepDirty = True
		self.updateModelTransform()

	def OnScaleReset(self):
		x = 1/numpy.linalg.norm(self.matrix[::,0].getA().flatten())
		y = 1/numpy.linalg.norm(self.matrix[::,1].getA().flatten())
		z = 1/numpy.linalg.norm(self.matrix[::,2].getA().flatten())
		self.matrix *= numpy.matrix([[x,0,0],[0,y,0],[0,0,z]], numpy.float64)
		for obj in self.objectList:
			obj.steepDirty = True
		self.updateModelTransform()

	def OnLayFlat(self):
		transformedVertexes = (numpy.matrix(self.objectList[0].mesh.vertexes, copy = False) * self.matrix).getA()
		minZvertex = transformedVertexes[transformedVertexes.argmin(0)[2]]
		dotMin = 1.0
		dotV = None
		for v in transformedVertexes:
			diff = v - minZvertex
			len = math.sqrt(diff[0] * diff[0] + diff[1] * diff[1] + diff[2] * diff[2])
			if len < 5:
				continue
			dot = (diff[2] / len)
			if dotMin > dot:
				dotMin = dot
				dotV = diff
		if dotV is None:
			return
		rad = -math.atan2(dotV[1], dotV[0])
		self.matrix *= numpy.matrix([[math.cos(rad), math.sin(rad), 0], [-math.sin(rad), math.cos(rad), 0], [0,0,1]], numpy.float64)
		rad = -math.asin(dotMin)
		self.matrix *= numpy.matrix([[math.cos(rad), 0, math.sin(rad)], [0,1,0], [-math.sin(rad), 0, math.cos(rad)]], numpy.float64)


		transformedVertexes = (numpy.matrix(self.objectList[0].mesh.vertexes, copy = False) * self.matrix).getA()
		minZvertex = transformedVertexes[transformedVertexes.argmin(0)[2]]
		dotMin = 1.0
		dotV = None
		for v in transformedVertexes:
			diff = v - minZvertex
			len = math.sqrt(diff[1] * diff[1] + diff[2] * diff[2])
			if len < 5:
				continue
			dot = (diff[2] / len)
			if dotMin > dot:
				dotMin = dot
				dotV = diff
		if dotV is None:
			return
		if dotV[1] < 0:
			rad = math.asin(dotMin)
		else:
			rad = -math.asin(dotMin)
		self.matrix *= numpy.matrix([[1,0,0], [0, math.cos(rad), math.sin(rad)], [0, -math.sin(rad), math.cos(rad)]], numpy.float64)

		for obj in self.objectList:
			obj.steepDirty = True
		self.updateModelTransform()

	def setViewMode(self, mode):
		if mode == "Normal":
			self.viewSelection.setValue(0)
		if mode == "GCode":
			self.viewSelection.setValue(4)
		wx.CallAfter(self.glCanvas.Refresh)

	def loadModelFiles(self, filelist, showWarning = False):
		while len(filelist) > len(self.objectList):
			self.objectList.append(previewObject())
		for idx in xrange(len(filelist), len(self.objectList)):
			self.objectList[idx].mesh = None
			self.objectList[idx].filename = None
		for idx in xrange(0, len(filelist)):
			obj = self.objectList[idx]
			if obj.filename != filelist[idx]:
				obj.fileTime = None
				self.gcodeFileTime = None
				self.logFileTime = None
				obj.mesh = None
			obj.filename = filelist[idx]

		self.deselectTool()
		self.gcodeFilename = sliceRun.getExportFilename(filelist[0])
		self.gcode = None
		#Do the STL file loading in a background thread so we don't block the UI.
		if self.loadThread is not None and self.loadThread.isAlive():
			self.abortLoading = True
			self.loadThread.join()
		self.abortLoading = False
		self.loadThread = threading.Thread(target=self.doFileLoadThread)
		self.loadThread.daemon = True
		self.loadThread.start()
		
		if showWarning:
			if (self.matrix - numpy.matrix([[1,0,0],[0,1,0],[0,0,1]], numpy.float64)).any() or len(profile.getPluginConfig()) > 0:
				self.ShowWarningPopup('Reset scale, rotation, mirror and plugins?', self.OnResetAll)
	
	def OnCheckReloadFile(self, e):
		#Only show the reload popup when the window has focus, because the popup goes over other programs.
		if self.GetParent().FindFocus() is None:
			return
		for obj in self.objectList:
			if obj.filename is not None and os.path.isfile(obj.filename) and obj.fileTime != os.stat(obj.filename).st_mtime:
				self.checkReloadFileTimer.Stop()
				self.ShowWarningPopup('File changed, reload?', self.reloadModelFiles)
		if wx.TheClipboard.Open():
			data = wx.TextDataObject()
			if wx.TheClipboard.GetData(data):
				data = data.GetText()
				if re.match('^http://.*/.*$', data):
					if data.endswith(tuple(meshLoader.supportedExtensions())):
						#Got an url on the clipboard with a model file.
						pass
			wx.TheClipboard.Close()
	
	def reloadModelFiles(self, filelist = None):
		if filelist is not None:
			#Only load this again if the filename matches the file we have already loaded (for auto loading GCode after slicing)
			for idx in xrange(0, len(filelist)):
				if self.objectList[idx].filename != filelist[idx]:
					return False
		else:
			filelist = []
			for idx in xrange(0, len(self.objectList)):
				filelist.append(self.objectList[idx].filename)
		self.loadModelFiles(filelist)
		return True
	
	def doFileLoadThread(self):
		for obj in self.objectList:
			if obj.filename is not None and os.path.isfile(obj.filename) and obj.fileTime != os.stat(obj.filename).st_mtime:
				obj.fileTime = os.stat(obj.filename).st_mtime
				try:
					mesh = meshLoader.loadMesh(obj.filename)
				except:
					wx.CallAfter(self.ShowWarningPopup, 'Failed to load %s' % (obj.filename))
					obj.mesh = None
					obj.filename = None
				else:
					obj.mesh = mesh
				obj.dirty = True
				obj.steepDirty = True
				self.updateModelTransform()
				if self.objectsBoundaryCircleSize is not None:
					self.glCanvas.zoom = self.objectsBoundaryCircleSize * 6.0
				self.errorList = []
				wx.CallAfter(self.updateToolbar)
				wx.CallAfter(self.glCanvas.Refresh)
			elif obj.filename is None or not os.path.isfile(obj.filename):
				obj.mesh = None
				obj.filename = None

		if os.path.isfile(self.gcodeFilename) and self.gcodeFileTime != os.stat(self.gcodeFilename).st_mtime:
			self.gcodeFileTime = os.stat(self.gcodeFilename).st_mtime
			self.gcodeDirty = True
			self.gcode = gcodeInterpreter.gcode()
			self.gcode.progressCallback = self.loadProgress
			self.gcode.load(self.gcodeFilename)

			errorList = []
			for line in open(self.gcodeFilename, "rt"):
				res = re.search(';Model error\(([a-z ]*)\): \(([0-9\.\-e]*), ([0-9\.\-e]*), ([0-9\.\-e]*)\) \(([0-9\.\-e]*), ([0-9\.\-e]*), ([0-9\.\-e]*)\)', line)
				if res is not None:
					v1 = util3d.Vector3(float(res.group(2)), float(res.group(3)), float(res.group(4)))
					v2 = util3d.Vector3(float(res.group(5)), float(res.group(6)), float(res.group(7)))
					errorList.append([v1, v2])
			self.errorList = errorList

			wx.CallAfter(self.updateToolbar)
			wx.CallAfter(self.glCanvas.Refresh)
		elif not os.path.isfile(self.gcodeFilename):
			self.gcode = None
		wx.CallAfter(self.checkReloadFileTimer.Start, 1000)
	
	def loadProgress(self, progress):
		if self.gcode is None:
			return True
		if self.layerSelect.getValue() == self.layerSelect.getMaxValue():
			self.layerSelect.setRange(1, len(self.gcode.layerList) - 1)
			self.layerSelect.setValue(self.layerSelect.getMaxValue())
		else:
			self.layerSelect.setRange(1, len(self.gcode.layerList) - 1)
		return self.abortLoading

	def OnResetAll(self, e = None):
		profile.putProfileSetting('model_matrix', '1,0,0,0,1,0,0,0,1')
		profile.setPluginConfig([])
		self.updateProfileToControls()

	def ShowWarningPopup(self, text, callback = None):
		self.warningPopup.text.SetLabel(text)
		self.warningPopup.callback = callback
		if callback is None:
			self.warningPopup.yesButton.Show(False)
			self.warningPopup.noButton.SetLabel('ok')
		else:
			self.warningPopup.yesButton.Show(True)
			self.warningPopup.noButton.SetLabel('no')
		self.warningPopup.Fit()
		self.warningPopup.Layout()
		self.OnMove()
		self.warningPopup.Show(True)
		self.warningPopup.timer.Start(5000)
	
	def OnWarningPopup(self, e):
		self.warningPopup.Show(False)
		self.warningPopup.timer.Stop()
		self.warningPopup.callback()

	def OnHideWarning(self, e):
		self.warningPopup.Show(False)
		self.warningPopup.timer.Stop()

	def updateToolbar(self):
		self.sliceButton.setDisabled(len(self.objectList) < 1 or self.objectList[0].mesh is None)
		self.printButton.setDisabled(self.gcode is None)
		self.rotateToolButton.setHidden(self.glCanvas.viewMode == "GCode")
		self.scaleToolButton.setHidden(self.glCanvas.viewMode == "GCode")
		self.mirrorToolButton.setHidden(self.glCanvas.viewMode == "GCode")
		if self.gcode is not None:
			self.layerSelect.setRange(1, len(self.gcode.layerList) - 1)
		self.Update()
	
	def OnViewChange(self):
		selection = self.viewSelection.getValue()
		self.glCanvas.drawSteepOverhang = False
		self.glCanvas.drawBorders = False
		if selection == 0:
			self.glCanvas.viewMode = "Normal"
		elif selection == 1:
			self.glCanvas.viewMode = "Transparent"
		elif selection == 2:
			self.glCanvas.viewMode = "X-Ray"
		elif selection == 3:
			self.glCanvas.viewMode = "Normal"
			self.glCanvas.drawSteepOverhang = True
		elif selection == 4:
			self.layerSelect.setValue(self.layerSelect.getMaxValue())
			self.glCanvas.viewMode = "GCode"
		elif selection == 5:
			self.glCanvas.viewMode = "Mixed"
		self.layerSelect.setHidden(self.glCanvas.viewMode != "GCode")
		self.updateToolbar()
		self.deselectTool()
		self.glCanvas.Refresh()

	def deselectTool(self):
		self.rotateToolButton.setSelected(False)
		self.scaleToolButton.setSelected(False)
		self.mirrorToolButton.setSelected(False)
		self.OnToolSelect()

	def updateModelTransform(self, f=0):
		if len(self.objectList) < 1 or self.objectList[0].mesh is None:
			return

		profile.putProfileSetting('model_matrix', ','.join(map(str, list(self.matrix.getA().flatten()))))
		for obj in self.objectList:
			if obj.mesh is None:
				continue
			obj.mesh.matrix = self.matrix
			obj.mesh.processMatrix()

		minV = self.objectList[0].mesh.getMinimum()
		maxV = self.objectList[0].mesh.getMaximum()
		objectsBoundaryCircleSize = self.objectList[0].mesh.boundaryCircleSize
		for obj in self.objectList:
			if obj.mesh is None:
				continue

			minV = numpy.minimum(minV, obj.mesh.getMinimum())
			maxV = numpy.maximum(maxV, obj.mesh.getMaximum())
			objectsBoundaryCircleSize = max(objectsBoundaryCircleSize, obj.mesh.boundaryCircleSize)

		self.objectsMaxV = maxV
		self.objectsMinV = minV
		self.objectsSize = self.objectsMaxV - self.objectsMinV
		self.objectsBoundaryCircleSize = objectsBoundaryCircleSize

		scaleX = numpy.linalg.norm(self.matrix[::,0].getA().flatten())
		scaleY = numpy.linalg.norm(self.matrix[::,1].getA().flatten())
		scaleZ = numpy.linalg.norm(self.matrix[::,2].getA().flatten())
		self.scaleXctrl.setValue(round(scaleX, 2))
		self.scaleYctrl.setValue(round(scaleY, 2))
		self.scaleZctrl.setValue(round(scaleZ, 2))
		self.scaleXmmctrl.setValue(round(self.objectsSize[0], 2))
		self.scaleYmmctrl.setValue(round(self.objectsSize[1], 2))
		self.scaleZmmctrl.setValue(round(self.objectsSize[2], 2))

		self.glCanvas.Refresh()
	
	def updateProfileToControls(self):
		self.matrix = numpy.matrix(numpy.array(profile.getObjectMatrix(), numpy.float64).reshape((3,3,)))
		self.updateModelTransform()
		for obj in self.objectList:
			obj.steepDirty = True
		self.glCanvas.updateProfileToControls()

class PreviewGLCanvas(openglGui.glGuiPanel):
	def __init__(self, parent):
		super(PreviewGLCanvas, self).__init__(parent)
		wx.EVT_MOUSEWHEEL(self, self.OnMouseWheel)
		self.parent = parent
		self.yaw = 30
		self.pitch = 60
		self.zoom = 300
		self.viewTarget = [parent.machineCenter.x, parent.machineCenter.y, 0.0]
		self.view3D = True
		self.gcodeDisplayList = []
		self.gcodeQuickDisplayList = []
		self.gcodeDisplayListMade = 0
		self.gcodeQuickDisplayListMade = 0
		self.objColor = [[1.0, 0.8, 0.6, 1.0], [0.2, 1.0, 0.1, 1.0], [1.0, 0.2, 0.1, 1.0], [0.1, 0.2, 1.0, 1.0]]
		self.oldX = 0
		self.oldY = 0
		self.dragType = ''
		self.tempMatrix = None
		self.viewport = None

	def updateProfileToControls(self):
		self.objColor[0] = profile.getPreferenceColour('model_colour')
		self.objColor[1] = profile.getPreferenceColour('model_colour2')
		self.objColor[2] = profile.getPreferenceColour('model_colour3')
		self.objColor[3] = profile.getPreferenceColour('model_colour4')

	def OnMouseMotion(self,e):
		if self.parent.objectsMaxV is not None and self.viewport is not None and self.viewMode != 'GCode' and self.viewMode != 'Mixed':
			p0 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 0, self.modelMatrix, self.projMatrix, self.viewport)
			p1 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 1, self.modelMatrix, self.projMatrix, self.viewport)
			p0 -= self.viewTarget
			p1 -= self.viewTarget
			if not e.Dragging() or self.dragType != 'tool':
				self.parent.tool.OnMouseMove(p0, p1)
		else:
			p0 = [0,0,0]
			p1 = [1,0,0]

		if e.Dragging() and e.LeftIsDown():
			if self.dragType == '':
				#Define the drag type depending on the cursor position.
				self.dragType = 'viewRotate'
				if self.viewMode != 'GCode' and self.viewMode != 'Mixed':
					if self.parent.tool.OnDragStart(p0, p1):
						self.dragType = 'tool'

			if self.dragType == 'viewRotate':
				if self.view3D:
					self.yaw += e.GetX() - self.oldX
					self.pitch -= e.GetY() - self.oldY
					if self.pitch > 170:
						self.pitch = 170
					if self.pitch < 10:
						self.pitch = 10
				else:
					self.viewTarget[0] -= float(e.GetX() - self.oldX) * self.zoom / self.GetSize().GetHeight() * 2
					self.viewTarget[1] += float(e.GetY() - self.oldY) * self.zoom / self.GetSize().GetHeight() * 2
			elif self.dragType == 'tool':
				self.parent.tool.OnDrag(p0, p1)

			#Workaround for buggy ATI cards.
			size = self.GetSizeTuple()
			self.SetSize((size[0]+1, size[1]))
			self.SetSize((size[0], size[1]))
			self.Refresh()
		else:
			if self.dragType != '':
				if self.tempMatrix is not None:
					self.parent.matrix *= self.tempMatrix
					self.parent.updateModelTransform()
					self.tempMatrix = None
					for obj in self.parent.objectList:
						obj.steepDirty = True
				self.parent.tool.OnDragEnd()
				self.dragType = ''
		if e.Dragging() and e.RightIsDown():
			self.zoom += e.GetY() - self.oldY
			if self.zoom < 1:
				self.zoom = 1
			if self.zoom > 500:
				self.zoom = 500
		self.oldX = e.GetX()
		self.oldY = e.GetY()

	def getObjectBoundaryCircle(self):
		return self.parent.objectsBoundaryCircleSize

	def getObjectSize(self):
		return self.parent.objectsSize

	def getObjectMatrix(self):
		return self.parent.matrix

	def getObjectCenterPos(self):
		return [self.parent.machineCenter.x, self.parent.machineCenter.y, self.parent.objectsSize[2] / 2 - profile.getProfileSettingFloat('object_sink')]

	def OnMouseWheel(self,e):
		self.zoom *= 1.0 - float(e.GetWheelRotation() / e.GetWheelDelta()) / 10.0
		if self.zoom < 1.0:
			self.zoom = 1.0
		if self.zoom > 500:
			self.zoom = 500
		self.Refresh()

	def OnKeyChar(self, keycode):
		if keycode == wx.WXK_UP:
			self.parent.layerSelect.setValue(self.parent.layerSelect.getValue() + 1)
			self.Refresh()
		elif keycode == wx.WXK_DOWN:
			self.parent.layerSelect.setValue(self.parent.layerSelect.getValue() - 1)
			self.Refresh()
		elif keycode == wx.WXK_PAGEUP:
			self.parent.layerSelect.setValue(self.parent.layerSelect.getValue() + 10)
			self.Refresh()
		elif keycode == wx.WXK_PAGEDOWN:
			self.parent.layerSelect.setValue(self.parent.layerSelect.getValue() - 10)
			self.Refresh()

	def OnPaint(self,e):
		opengl.InitGL(self, self.view3D, self.zoom)
		if self.view3D:
			glTranslate(0,0,-self.zoom)
			glTranslate(self.zoom/20.0,0,0)
			glRotate(-self.pitch, 1,0,0)
			glRotate(self.yaw, 0,0,1)

			if self.viewMode == "GCode" or self.viewMode == "Mixed":
				n = min(self.gcodeQuickDisplayListMade, self.parent.layerSelect.getValue())
				if self.parent.gcode is not None and -1 < n < len(self.parent.gcode.layerList) and len(self.parent.gcode.layerList[n]) > 0:
					self.viewTarget[2] = self.parent.gcode.layerList[n][0].list[-1].z
			else:
				if self.parent.objectsMaxV is not None:
					self.viewTarget = self.getObjectCenterPos()
		glTranslate(-self.viewTarget[0], -self.viewTarget[1], -self.viewTarget[2])

		self.viewport = glGetIntegerv(GL_VIEWPORT)
		self.modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
		self.projMatrix = glGetDoublev(GL_PROJECTION_MATRIX)

		self.OnDraw()

		if len(self.parent.objectList) > 0 and self.parent.objectList[0].mesh is None and self.parent.objectList[0].filename is not None:
			glDisable(GL_DEPTH_TEST)
			glLoadIdentity()
			glColor3ub(255,255,255)
			glTranslate(0, -3, -10)
			opengl.glDrawStringCenter('Loading %s ...' % (os.path.basename(self.parent.objectList[0].filename)))

	def OnDraw(self):
		machineSize = self.parent.machineSize

		if self.parent.gcode is not None and (self.viewMode == "GCode" or self.viewMode == "Mixed"):
			if self.parent.gcodeDirty:
				self.parent.gcodeDirty = False
				self.gcodeDisplayListMade = 0
				self.gcodeQuickDisplayListMade = 0

			if self.gcodeDisplayListMade < len(self.parent.gcode.layerList):
				gcodeGenStartTime = time.time()
				while time.time() - gcodeGenStartTime < 0.1 and self.gcodeQuickDisplayListMade < len(self.parent.gcode.layerList):
					if len(self.gcodeQuickDisplayList) == self.gcodeQuickDisplayListMade:
						self.gcodeQuickDisplayList.append(glGenLists(1))
					glNewList(self.gcodeQuickDisplayList[self.gcodeQuickDisplayListMade], GL_COMPILE)
					opengl.DrawGCodeLayer(self.parent.gcode.layerList[self.gcodeQuickDisplayListMade], True)
					glEndList()
					self.gcodeQuickDisplayListMade += 1
				while time.time() - gcodeGenStartTime < 0.1 and self.gcodeDisplayListMade < len(self.parent.gcode.layerList):
					if len(self.gcodeDisplayList) == self.gcodeDisplayListMade:
						self.gcodeDisplayList.append(glGenLists(1))
					glNewList(self.gcodeDisplayList[self.gcodeDisplayListMade], GL_COMPILE)
					opengl.DrawGCodeLayer(self.parent.gcode.layerList[self.gcodeDisplayListMade], False)
					glEndList()
					self.gcodeDisplayListMade += 1
				wx.CallAfter(self.Refresh)
		
		glPushMatrix()
		glTranslate(self.parent.machineCenter.x, self.parent.machineCenter.y, -profile.getProfileSettingFloat('object_sink'))
		for obj in self.parent.objectList:
			if obj.mesh is None:
				continue
			if obj.displayList is None:
				obj.displayList = glGenLists(1)
				obj.steepDisplayList = glGenLists(1)
				obj.outlineDisplayList = glGenLists(1)
			if obj.dirty:
				obj.dirty = False
				glNewList(obj.displayList, GL_COMPILE)
				opengl.DrawMesh(obj.mesh, numpy.linalg.det(obj.mesh.matrix) < 0)
				glEndList()
				glNewList(obj.outlineDisplayList, GL_COMPILE)
				opengl.DrawMeshOutline(obj.mesh)
				glEndList()

			if self.viewMode == "Mixed":
				glDisable(GL_BLEND)
				glColor3f(0.0,0.0,0.0)
				self.drawModel(obj.displayList)
				glColor3f(1.0,1.0,1.0)
				glClear(GL_DEPTH_BUFFER_BIT)
		
		glPopMatrix()
		
		if self.parent.gcode is not None and (self.viewMode == "GCode" or self.viewMode == "Mixed"):
			glPushMatrix()
			if profile.getPreference('machine_center_is_zero') == 'True':
				glTranslate(self.parent.machineCenter.x, self.parent.machineCenter.y, 0)
			glEnable(GL_COLOR_MATERIAL)
			glEnable(GL_LIGHTING)
			drawQuickUpToLayer = min(self.gcodeQuickDisplayListMade, self.parent.layerSelect.getValue() + 1)
			drawUpToLayer = min(self.gcodeDisplayListMade, self.parent.layerSelect.getValue() + 1)

			for i in xrange(drawQuickUpToLayer - 1, -1, -1):
				c = 1.0
				if i < self.parent.layerSelect.getValue():
					c = 0.9 - (drawQuickUpToLayer - i) * 0.1
					if c < 0.4:
						c = (0.4 + c) / 2
					if c < 0.1:
						c = 0.1
				glLightfv(GL_LIGHT0, GL_DIFFUSE, [0,0,0,0])
				glLightfv(GL_LIGHT0, GL_AMBIENT, [c,c,c,c])
				if self.gcodeDisplayListMade > i and drawUpToLayer - i < 15:
					glCallList(self.gcodeDisplayList[i])
				else:
					glCallList(self.gcodeQuickDisplayList[i])

			glDisable(GL_LIGHTING)
			glDisable(GL_COLOR_MATERIAL)
			glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0]);
			glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0]);
			glPopMatrix()

		glColor3f(1.0,1.0,1.0)
		glPushMatrix()
		glTranslate(self.parent.machineCenter.x, self.parent.machineCenter.y, -profile.getProfileSettingFloat('object_sink'))
		for obj in self.parent.objectList:
			if obj.mesh is None:
				continue

			if self.viewMode == "Transparent" or self.viewMode == "Mixed":
				glLightfv(GL_LIGHT0, GL_DIFFUSE, map(lambda x: x / 2, self.objColor[self.parent.objectList.index(obj)]))
				glLightfv(GL_LIGHT0, GL_AMBIENT, map(lambda x: x / 10, self.objColor[self.parent.objectList.index(obj)]))
				#If we want transparent, then first render a solid black model to remove the printer size lines.
				if self.viewMode != "Mixed":
					glDisable(GL_BLEND)
					glColor3f(0.0,0.0,0.0)
					self.drawModel(obj.displayList)
					glColor3f(1.0,1.0,1.0)
				#After the black model is rendered, render the model again but now with lighting and no depth testing.
				glDisable(GL_DEPTH_TEST)
				glEnable(GL_LIGHTING)
				glEnable(GL_BLEND)
				glBlendFunc(GL_ONE, GL_ONE)
				glEnable(GL_LIGHTING)
				self.drawModel(obj.displayList)
				glEnable(GL_DEPTH_TEST)
			elif self.viewMode == "X-Ray":
				glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
				glDisable(GL_LIGHTING)
				glDisable(GL_DEPTH_TEST)
				glEnable(GL_STENCIL_TEST)
				glStencilFunc(GL_ALWAYS, 1, 1)
				glStencilOp(GL_INCR, GL_INCR, GL_INCR)
				self.drawModel(obj.displayList)
				glStencilOp (GL_KEEP, GL_KEEP, GL_KEEP);
				
				glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
				glStencilFunc(GL_EQUAL, 0, 1)
				glColor(1, 1, 1)
				self.drawModel(obj.displayList)
				glStencilFunc(GL_EQUAL, 1, 1)
				glColor(1, 0, 0)
				self.drawModel(obj.displayList)

				glPushMatrix()
				glLoadIdentity()
				for i in xrange(2, 15, 2):
					glStencilFunc(GL_EQUAL, i, 0xFF);
					glColor(float(i)/10, float(i)/10, float(i)/5)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-1)
					glVertex3f( 1000,-1000,-1)
					glVertex3f( 1000, 1000,-1)
					glVertex3f(-1000, 1000,-1)
					glEnd()
				for i in xrange(1, 15, 2):
					glStencilFunc(GL_EQUAL, i, 0xFF);
					glColor(float(i)/10, 0, 0)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-1)
					glVertex3f( 1000,-1000,-1)
					glVertex3f( 1000, 1000,-1)
					glVertex3f(-1000, 1000,-1)
					glEnd()
				glPopMatrix()

				glDisable(GL_STENCIL_TEST)
				glEnable(GL_DEPTH_TEST)
				
				#Fix the depth buffer
				glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
				self.drawModel(obj.displayList)
				glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
			elif self.viewMode == "Normal":
				glLightfv(GL_LIGHT0, GL_DIFFUSE, self.objColor[self.parent.objectList.index(obj)])
				glLightfv(GL_LIGHT0, GL_AMBIENT, map(lambda x: x * 0.4, self.objColor[self.parent.objectList.index(obj)]))
				glEnable(GL_LIGHTING)
				self.drawModel(obj.displayList)

			if self.drawBorders and (self.viewMode == "Normal" or self.viewMode == "Transparent" or self.viewMode == "X-Ray"):
				glEnable(GL_DEPTH_TEST)
				glDisable(GL_LIGHTING)
				glColor3f(1,1,1)
				self.drawModel(obj.outlineDisplayList)

			if self.drawSteepOverhang:
				if obj.steepDirty:
					obj.steepDirty = False
					glNewList(obj.steepDisplayList, GL_COMPILE)
					opengl.DrawMeshSteep(obj.mesh, self.parent.matrix, 60)
					glEndList()
				glDisable(GL_LIGHTING)
				glColor3f(1,1,1)
				self.drawModel(obj.steepDisplayList)

		glPopMatrix()	
		#if self.viewMode == "Normal" or self.viewMode == "Transparent" or self.viewMode == "X-Ray":
		#	glDisable(GL_LIGHTING)
		#	glDisable(GL_DEPTH_TEST)
		#	glDisable(GL_BLEND)
		#	glColor3f(1,0,0)
		#	glBegin(GL_LINES)
		#	for err in self.parent.errorList:
		#		glVertex3f(err[0].x, err[0].y, err[0].z)
		#		glVertex3f(err[1].x, err[1].y, err[1].z)
		#	glEnd()
		#	glEnable(GL_DEPTH_TEST)

		opengl.DrawMachine(machineSize)

		#Draw the current selected tool
		if self.parent.objectsMaxV is not None and self.viewMode != 'GCode' and self.viewMode != 'Mixed':
			glPushMatrix()
			pos = self.getObjectCenterPos()
			glTranslate(pos[0], pos[1], pos[2])
			self.parent.tool.OnDraw()
			glPopMatrix()

	def drawModel(self, displayList):
		vMin = self.parent.objectsMinV
		vMax = self.parent.objectsMaxV
		if vMin is None:
			return
		offset = - vMin - (vMax - vMin) / 2

		matrix = opengl.convert3x3MatrixTo4x4(self.parent.matrix)

		glPushMatrix()
		glTranslate(0, 0, self.parent.objectsSize[2]/2)
		if self.tempMatrix is not None:
			tempMatrix = opengl.convert3x3MatrixTo4x4(self.tempMatrix)
			glMultMatrixf(tempMatrix)
		glTranslate(0, 0, -self.parent.objectsSize[2]/2)
		glTranslate(offset[0], offset[1], -vMin[2])
		glMultMatrixf(matrix)
		glCallList(displayList)
		glPopMatrix()
