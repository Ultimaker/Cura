from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import numpy
import time
import os
import traceback
import threading
import math

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.gui import printWindow
from Cura.util import profile
from Cura.util import meshLoader
from Cura.util import objectScene
from Cura.util import resources
from Cura.util import sliceEngine
from Cura.util import machineCom
from Cura.util import removableStorage
from Cura.util import gcodeInterpreter
from Cura.gui.util import previewTools
from Cura.gui.util import opengl
from Cura.gui.util import openglGui
from Cura.gui.tools import youmagineGui

class SceneView(openglGui.glGuiPanel):
	def __init__(self, parent):
		super(SceneView, self).__init__(parent)

		self._yaw = 30
		self._pitch = 60
		self._zoom = 300
		self._scene = objectScene.Scene()
		self._gcode = None
		self._gcodeVBOs = []
		self._gcodeFilename = None
		self._gcodeLoadThread = None
		self._objectShader = None
		self._objectLoadShader = None
		self._focusObj = None
		self._selectedObj = None
		self._objColors = [None,None,None,None]
		self._mouseX = -1
		self._mouseY = -1
		self._mouseState = None
		self._viewTarget = numpy.array([0,0,0], numpy.float32)
		self._animView = None
		self._animZoom = None
		self._platformMesh = {}
		self._isSimpleMode = True
		self._usbPrintMonitor = printWindow.printProcessMonitor(lambda : self._queueRefresh())

		self._viewport = None
		self._modelMatrix = None
		self._projMatrix = None
		self.tempMatrix = None

		self.openFileButton      = openglGui.glButton(self, 4, _("Load"), (0,0), self.showLoadModel)
		self.printButton         = openglGui.glButton(self, 6, _("Print"), (1,0), self.OnPrintButton)
		self.printButton.setDisabled(True)

		group = []
		self.rotateToolButton = openglGui.glRadioButton(self, 8, _("Rotate"), (0,-1), group, self.OnToolSelect)
		self.scaleToolButton  = openglGui.glRadioButton(self, 9, _("Scale"), (1,-1), group, self.OnToolSelect)
		self.mirrorToolButton  = openglGui.glRadioButton(self, 10, _("Mirror"), (2,-1), group, self.OnToolSelect)

		self.resetRotationButton = openglGui.glButton(self, 12, _("Reset"), (0,-2), self.OnRotateReset)
		self.layFlatButton       = openglGui.glButton(self, 16, _("Lay flat"), (0,-3), self.OnLayFlat)

		self.resetScaleButton    = openglGui.glButton(self, 13, _("Reset"), (1,-2), self.OnScaleReset)
		self.scaleMaxButton      = openglGui.glButton(self, 17, _("To max"), (1,-3), self.OnScaleMax)

		self.mirrorXButton       = openglGui.glButton(self, 14, _("Mirror X"), (2,-2), lambda button: self.OnMirror(0))
		self.mirrorYButton       = openglGui.glButton(self, 18, _("Mirror Y"), (2,-3), lambda button: self.OnMirror(1))
		self.mirrorZButton       = openglGui.glButton(self, 22, _("Mirror Z"), (2,-4), lambda button: self.OnMirror(2))

		self.rotateToolButton.setExpandArrow(True)
		self.scaleToolButton.setExpandArrow(True)
		self.mirrorToolButton.setExpandArrow(True)

		self.scaleForm = openglGui.glFrame(self, (2, -2))
		openglGui.glGuiLayoutGrid(self.scaleForm)
		openglGui.glLabel(self.scaleForm, _("Scale X"), (0,0))
		self.scaleXctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,0), lambda value: self.OnScaleEntry(value, 0))
		openglGui.glLabel(self.scaleForm, _("Scale Y"), (0,1))
		self.scaleYctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,1), lambda value: self.OnScaleEntry(value, 1))
		openglGui.glLabel(self.scaleForm, _("Scale Z"), (0,2))
		self.scaleZctrl = openglGui.glNumberCtrl(self.scaleForm, '1.0', (1,2), lambda value: self.OnScaleEntry(value, 2))
		openglGui.glLabel(self.scaleForm, _("Size X (mm)"), (0,4))
		self.scaleXmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,4), lambda value: self.OnScaleEntryMM(value, 0))
		openglGui.glLabel(self.scaleForm, _("Size Y (mm)"), (0,5))
		self.scaleYmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,5), lambda value: self.OnScaleEntryMM(value, 1))
		openglGui.glLabel(self.scaleForm, _("Size Z (mm)"), (0,6))
		self.scaleZmmctrl = openglGui.glNumberCtrl(self.scaleForm, '0.0', (1,6), lambda value: self.OnScaleEntryMM(value, 2))
		openglGui.glLabel(self.scaleForm, _("Uniform scale"), (0,8))
		self.scaleUniform = openglGui.glCheckbox(self.scaleForm, True, (1,8), None)

		self.viewSelection = openglGui.glComboButton(self, _("View mode"), [7,19,11,15,23], [_("Normal"), _("Overhang"), _("Transparent"), _("X-Ray"), _("Layers")], (-1,0), self.OnViewChange)
		self.layerSelect = openglGui.glSlider(self, 10000, 0, 1, (-1,-2), lambda : self.QueueRefresh())

		self.youMagineButton = openglGui.glButton(self, 26, _("Share on YouMagine"), (2,0), lambda button: youmagineGui.youmagineManager(self.GetTopLevelParent(), self._scene))
		self.youMagineButton.setDisabled(True)

		self.notification = openglGui.glNotification(self, (0, 0))

		self._slicer = sliceEngine.Slicer(self._updateSliceProgress)
		self._sceneUpdateTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self._onRunSlicer, self._sceneUpdateTimer)
		self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

		self.OnViewChange()
		self.OnToolSelect(0)
		self.updateToolButtons()
		self.updateProfileToControls()

	def loadGCodeFile(self, filename):
		self.OnDeleteAll(None)
		if self._gcode is not None:
			self._gcode = None
			for layerVBOlist in self._gcodeVBOs:
				for vbo in layerVBOlist:
					self.glReleaseList.append(vbo)
			self._gcodeVBOs = []
		self._gcode = gcodeInterpreter.gcode()
		self._gcodeFilename = filename
		self.printButton.setBottomText('')
		self.viewSelection.setValue(4)
		self.printButton.setDisabled(False)
		self.youMagineButton.setDisabled(True)
		self.OnViewChange()

	def loadSceneFiles(self, filenames):
		self.youMagineButton.setDisabled(False)
		if self.viewSelection.getValue() == 4:
			self.viewSelection.setValue(0)
			self.OnViewChange()
		self.loadScene(filenames)

	def loadFiles(self, filenames):
		gcodeFilename = None
		for filename in filenames:
			self.GetParent().GetParent().GetParent().addToModelMRU(filename)        #??? only Model files?
			ext = filename[filename.rfind('.')+1:].upper()
			if ext == 'G' or ext == 'GCODE':
				gcodeFilename = filename
		if gcodeFilename is not None:
			self.loadGCodeFile(gcodeFilename)
		else:
			profileFilename = None
			for filename in filenames:
				ext = filename[filename.rfind('.')+1:].upper()
				if ext == 'INI':
					profileFilename = filename
			if profileFilename is not None:
				profile.loadProfile(profileFilename)
				self.GetParent().GetParent().GetParent().updateProfileToAllControls()
			else:
				self.loadSceneFiles(filenames)

	def showLoadModel(self, button = 1):
		if button == 1:
			dlg=wx.FileDialog(self, _("Open 3D model"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_MULTIPLE)
			dlg.SetWildcard(meshLoader.loadWildcardFilter() + "|GCode file (*.gcode)|*.g;*.gcode;*.G;*.GCODE")
			if dlg.ShowModal() != wx.ID_OK:
				dlg.Destroy()
				return
			filenames = dlg.GetPaths()
			dlg.Destroy()
			if len(filenames) < 1:
				return False
			profile.putPreference('lastFile', filenames[0])
			self.loadFiles(filenames)

	def showSaveModel(self):
		if len(self._scene.objects()) < 1:
			return
		dlg=wx.FileDialog(self, _("Save 3D model"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		dlg.SetWildcard(meshLoader.saveWildcardFilter())
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		filename = dlg.GetPath()
		dlg.Destroy()
		meshLoader.saveMeshes(filename, self._scene.objects())

	def OnPrintButton(self, button):
		if button == 1:
			if machineCom.machineIsConnected():
				self.showPrintWindow()
			elif len(removableStorage.getPossibleSDcardDrives()) > 0:
				drives = removableStorage.getPossibleSDcardDrives()
				if len(drives) > 1:
					dlg = wx.SingleChoiceDialog(self, "Select SD drive", "Multiple removable drives have been found,\nplease select your SD card drive", map(lambda n: n[0], drives))
					if dlg.ShowModal() != wx.ID_OK:
						dlg.Destroy()
						return
					drive = drives[dlg.GetSelection()]
					dlg.Destroy()
				else:
					drive = drives[0]
				filename = self._scene._objectList[0].getName() + '.gcode'
				threading.Thread(target=self._copyFile,args=(self._gcodeFilename, drive[1] + filename, drive[1])).start()
			else:
				self.showSaveGCode()
		if button == 3:
			menu = wx.Menu()
			self.Bind(wx.EVT_MENU, lambda e: self.showPrintWindow(), menu.Append(-1, _("Print with USB")))
			self.Bind(wx.EVT_MENU, lambda e: self.showSaveGCode(), menu.Append(-1, _("Save GCode...")))
			self.Bind(wx.EVT_MENU, lambda e: self._showSliceLog(), menu.Append(-1, _("Slice engine log...")))
			self.PopupMenu(menu)
			menu.Destroy()

	def showPrintWindow(self):
		if self._gcodeFilename is None:
			return
		self._usbPrintMonitor.loadFile(self._gcodeFilename, self._slicer.getID())
		if self._gcodeFilename == self._slicer.getGCodeFilename():
			self._slicer.submitSliceInfoOnline()

	def showSaveGCode(self):
		defPath = profile.getPreference('lastFile')
		defPath = defPath[0:defPath.rfind('.')] + '.gcode'
		dlg=wx.FileDialog(self, _("Save toolpath"), defPath, style=wx.FD_SAVE)
		dlg.SetFilename(self._scene._objectList[0].getName())
		dlg.SetWildcard('Toolpath (*.gcode)|*.gcode;*.g')
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		filename = dlg.GetPath()
		dlg.Destroy()

		threading.Thread(target=self._copyFile,args=(self._gcodeFilename, filename)).start()

	def _copyFile(self, fileA, fileB, allowEject = False):
		try:
			size = float(os.stat(fileA).st_size)
			with open(fileA, 'rb') as fsrc:
				with open(fileB, 'wb') as fdst:
					while 1:
						buf = fsrc.read(16*1024)
						if not buf:
							break
						fdst.write(buf)
						self.printButton.setProgressBar(float(fsrc.tell()) / size)
						self._queueRefresh()
		except:
			import sys
			print sys.exc_info()
			self.notification.message("Failed to save")
		else:
			if allowEject:
				self.notification.message("Saved as %s" % (fileB), lambda : self.notification.message('You can now eject the card.') if removableStorage.ejectDrive(allowEject) else self.notification.message('Safe remove failed...'))
			else:
				self.notification.message("Saved as %s" % (fileB))
		self.printButton.setProgressBar(None)
		if fileA == self._slicer.getGCodeFilename():
			self._slicer.submitSliceInfoOnline()

	def _showSliceLog(self):
		dlg = wx.TextEntryDialog(self, _("The slicing engine reported the following"), _("Engine log..."), '\n'.join(self._slicer.getSliceLog()), wx.TE_MULTILINE | wx.OK | wx.CENTRE)
		dlg.ShowModal()
		dlg.Destroy()

	def OnToolSelect(self, button):
		if self.rotateToolButton.getSelected():
			self.tool = previewTools.toolRotate(self)
		elif self.scaleToolButton.getSelected():
			self.tool = previewTools.toolScale(self)
		elif self.mirrorToolButton.getSelected():
			self.tool = previewTools.toolNone(self)
		else:
			self.tool = previewTools.toolNone(self)
		self.resetRotationButton.setHidden(not self.rotateToolButton.getSelected())
		self.layFlatButton.setHidden(not self.rotateToolButton.getSelected())
		self.resetScaleButton.setHidden(not self.scaleToolButton.getSelected())
		self.scaleMaxButton.setHidden(not self.scaleToolButton.getSelected())
		self.scaleForm.setHidden(not self.scaleToolButton.getSelected())
		self.mirrorXButton.setHidden(not self.mirrorToolButton.getSelected())
		self.mirrorYButton.setHidden(not self.mirrorToolButton.getSelected())
		self.mirrorZButton.setHidden(not self.mirrorToolButton.getSelected())

	def updateToolButtons(self):
		if self._selectedObj is None:
			hidden = True
		else:
			hidden = False
		self.rotateToolButton.setHidden(hidden)
		self.scaleToolButton.setHidden(hidden)
		self.mirrorToolButton.setHidden(hidden)
		if hidden:
			self.rotateToolButton.setSelected(False)
			self.scaleToolButton.setSelected(False)
			self.mirrorToolButton.setSelected(False)
			self.OnToolSelect(0)

	def OnViewChange(self):
		if self.viewSelection.getValue() == 4:
			self.viewMode = 'gcode'
			if self._gcode is not None and self._gcode.layerList is not None:
				self.layerSelect.setRange(1, len(self._gcode.layerList) - 1)
			self._selectObject(None)
		elif self.viewSelection.getValue() == 1:
			self.viewMode = 'overhang'
		elif self.viewSelection.getValue() == 2:
			self.viewMode = 'transparent'
		elif self.viewSelection.getValue() == 3:
			self.viewMode = 'xray'
		else:
			self.viewMode = 'normal'
		self.layerSelect.setHidden(self.viewMode != 'gcode')
		self.QueueRefresh()

	def OnRotateReset(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.resetRotation()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnLayFlat(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.layFlat()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnScaleReset(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.resetScale()
		self._selectObject(self._selectedObj)
		self.updateProfileToControls()
		self.sceneUpdated()

	def OnScaleMax(self, button):
		if self._selectedObj is None:
			return
		self._selectedObj.scaleUpTo(self._machineSize - numpy.array(profile.calculateObjectSizeOffsets() + [0.0], numpy.float32) * 2 - numpy.array([1,1,1], numpy.float32))
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.updateProfileToControls()
		self.sceneUpdated()

	def OnMirror(self, axis):
		if self._selectedObj is None:
			return
		self._selectedObj.mirror(axis)
		self.sceneUpdated()

	def OnScaleEntry(self, value, axis):
		if self._selectedObj is None:
			return
		try:
			value = float(value)
		except:
			return
		self._selectedObj.setScale(value, axis, self.scaleUniform.getValue())
		self.updateProfileToControls()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnScaleEntryMM(self, value, axis):
		if self._selectedObj is None:
			return
		try:
			value = float(value)
		except:
			return
		self._selectedObj.setSize(value, axis, self.scaleUniform.getValue())
		self.updateProfileToControls()
		self._scene.pushFree()
		self._selectObject(self._selectedObj)
		self.sceneUpdated()

	def OnDeleteAll(self, e):
		while len(self._scene.objects()) > 0:
			self._deleteObject(self._scene.objects()[0])
		self._animView = openglGui.animation(self, self._viewTarget.copy(), numpy.array([0,0,0], numpy.float32), 0.5)

	def OnMultiply(self, e):
		if self._focusObj is None:
			return
		obj = self._focusObj
		dlg = wx.NumberEntryDialog(self, "How many copies do you want?", "Copies", "Multiply", 1, 1, 100)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		cnt = dlg.GetValue()
		dlg.Destroy()
		n = 0
		while True:
			n += 1
			newObj = obj.copy()
			self._scene.add(newObj)
			self._scene.centerAll()
			if not self._scene.checkPlatform(newObj):
				break
			if n > cnt:
				break
		if n <= cnt:
			self.notification.message("Could not create more then %d items" % (n - 1))
		self._scene.remove(newObj)
		self._scene.centerAll()
		self.sceneUpdated()

	def OnSplitObject(self, e):
		if self._focusObj is None:
			return
		self._scene.remove(self._focusObj)
		for obj in self._focusObj.split(self._splitCallback):
			if numpy.max(obj.getSize()) > 2.0:
				self._scene.add(obj)
		self._scene.centerAll()
		self._selectObject(None)
		self.sceneUpdated()

	def OnCenter(self, e):
		if self._focusObj is None:
			return
		self._focusObj.setPosition(numpy.array([0.0, 0.0]))
		self._scene.pushFree()

	def _splitCallback(self, progress):
		print progress

	def OnMergeObjects(self, e):
		if self._selectedObj is None or self._focusObj is None or self._selectedObj == self._focusObj:
			if len(self._scene.objects()) == 2:
				self._scene.merge(self._scene.objects()[0], self._scene.objects()[1])
				self.sceneUpdated()
			return
		self._scene.merge(self._selectedObj, self._focusObj)
		self.sceneUpdated()

	def sceneUpdated(self):
		self._sceneUpdateTimer.Start(500, True)
		self._slicer.abortSlicer()
		self._scene.setSizeOffsets(numpy.array(profile.calculateObjectSizeOffsets(), numpy.float32))
		self.QueueRefresh()

	def _onRunSlicer(self, e):
		if self._isSimpleMode:
			self.GetTopLevelParent().simpleSettingsPanel.setupSlice()
		self._slicer.runSlicer(self._scene)
		if self._isSimpleMode:
			profile.resetTempOverride()

	def _updateSliceProgress(self, progressValue, ready):
		if not ready:
			if self.printButton.getProgressBar() is not None and progressValue >= 0.0 and abs(self.printButton.getProgressBar() - progressValue) < 0.01:
				return
		self.printButton.setDisabled(not ready)
		if progressValue >= 0.0:
			self.printButton.setProgressBar(progressValue)
		else:
			self.printButton.setProgressBar(None)
		if self._gcode is not None:
			self._gcode = None
			for layerVBOlist in self._gcodeVBOs:
				for vbo in layerVBOlist:
					self.glReleaseList.append(vbo)
			self._gcodeVBOs = []
		if ready:
			self.printButton.setProgressBar(None)
			cost = self._slicer.getFilamentCost()
			if cost is not None:
				self.printButton.setBottomText('%s\n%s\n%s' % (self._slicer.getPrintTime(), self._slicer.getFilamentAmount(), cost))
			else:
				self.printButton.setBottomText('%s\n%s' % (self._slicer.getPrintTime(), self._slicer.getFilamentAmount()))
			self._gcode = gcodeInterpreter.gcode()
			self._gcodeFilename = self._slicer.getGCodeFilename()
		else:
			self.printButton.setBottomText('')
		self.QueueRefresh()

	def _loadGCode(self):
		self._gcode.progressCallback = self._gcodeLoadCallback
		self._gcode.load(self._gcodeFilename)

	def _gcodeLoadCallback(self, progress):
		if self._gcode is None:
			return True
		if len(self._gcode.layerList) % 15 == 0:
			time.sleep(0.1)
		if self._gcode is None:
			return True
		self.layerSelect.setRange(1, len(self._gcode.layerList) - 1)
		if self.viewMode == 'gcode':
			self._queueRefresh()
		return False

	def loadScene(self, fileList):
		for filename in fileList:
			try:
				objList = meshLoader.loadMeshes(filename)
			except:
				traceback.print_exc()
			else:
				for obj in objList:
					if self._objectLoadShader is not None:
						obj._loadAnim = openglGui.animation(self, 1, 0, 1.5)
					else:
						obj._loadAnim = None
					self._scene.add(obj)
					self._scene.centerAll()
					self._selectObject(obj)
					if obj.getScale()[0] < 1.0:
						self.notification.message("Warning: Object scaled down.")
		self.sceneUpdated()

	def _deleteObject(self, obj):
		if obj == self._selectedObj:
			self._selectObject(None)
		if obj == self._focusObj:
			self._focusObj = None
		self._scene.remove(obj)
		for m in obj._meshList:
			if m.vbo is not None and m.vbo.decRef():
				self.glReleaseList.append(m.vbo)
		import gc
		gc.collect()
		self.sceneUpdated()

	def _selectObject(self, obj, zoom = True):
		if obj != self._selectedObj:
			self._selectedObj = obj
			self.updateProfileToControls()
			self.updateToolButtons()
		if zoom and obj is not None:
			newViewPos = numpy.array([obj.getPosition()[0], obj.getPosition()[1], obj.getMaximum()[2] / 2])
			self._animView = openglGui.animation(self, self._viewTarget.copy(), newViewPos, 0.5)
			newZoom = obj.getBoundaryCircle() * 6
			if newZoom > numpy.max(self._machineSize) * 3:
				newZoom = numpy.max(self._machineSize) * 3
			self._animZoom = openglGui.animation(self, self._zoom, newZoom, 0.5)

	def updateProfileToControls(self):
		oldSimpleMode = self._isSimpleMode
		self._isSimpleMode = profile.getPreference('startMode') == 'Simple'
		if self._isSimpleMode != oldSimpleMode:
			self._scene.arrangeAll()
			self.sceneUpdated()
		self._machineSize = numpy.array([profile.getMachineSettingFloat('machine_width'), profile.getMachineSettingFloat('machine_depth'), profile.getMachineSettingFloat('machine_height')])
		self._objColors[0] = profile.getPreferenceColour('model_colour')
		self._objColors[1] = profile.getPreferenceColour('model_colour2')
		self._objColors[2] = profile.getPreferenceColour('model_colour3')
		self._objColors[3] = profile.getPreferenceColour('model_colour4')
		self._scene.setMachineSize(self._machineSize)
		self._scene.setSizeOffsets(numpy.array(profile.calculateObjectSizeOffsets(), numpy.float32))
		self._scene.setHeadSize(profile.getMachineSettingFloat('extruder_head_size_min_x'), profile.getMachineSettingFloat('extruder_head_size_max_x'), profile.getMachineSettingFloat('extruder_head_size_min_y'), profile.getMachineSettingFloat('extruder_head_size_max_y'), profile.getMachineSettingFloat('extruder_head_size_height'))

		if self._selectedObj is not None:
			scale = self._selectedObj.getScale()
			size = self._selectedObj.getSize()
			self.scaleXctrl.setValue(round(scale[0], 2))
			self.scaleYctrl.setValue(round(scale[1], 2))
			self.scaleZctrl.setValue(round(scale[2], 2))
			self.scaleXmmctrl.setValue(round(size[0], 2))
			self.scaleYmmctrl.setValue(round(size[1], 2))
			self.scaleZmmctrl.setValue(round(size[2], 2))

	def OnKeyChar(self, keyCode):
		if keyCode == wx.WXK_DELETE or keyCode == wx.WXK_NUMPAD_DELETE:
			if self._selectedObj is not None:
				self._deleteObject(self._selectedObj)
				self.QueueRefresh()
		if keyCode == wx.WXK_UP:
			self.layerSelect.setValue(self.layerSelect.getValue() + 1)
			self.QueueRefresh()
		elif keyCode == wx.WXK_DOWN:
			self.layerSelect.setValue(self.layerSelect.getValue() - 1)
			self.QueueRefresh()
		elif keyCode == wx.WXK_PAGEUP:
			self.layerSelect.setValue(self.layerSelect.getValue() + 10)
			self.QueueRefresh()
		elif keyCode == wx.WXK_PAGEDOWN:
			self.layerSelect.setValue(self.layerSelect.getValue() - 10)
			self.QueueRefresh()

		if keyCode == wx.WXK_F3 and wx.GetKeyState(wx.WXK_SHIFT):
			shaderEditor(self, self.ShaderUpdate, self._objectLoadShader.getVertexShader(), self._objectLoadShader.getFragmentShader())
		if keyCode == wx.WXK_F4 and wx.GetKeyState(wx.WXK_SHIFT):
			from collections import defaultdict
			from gc import get_objects
			self._beforeLeakTest = defaultdict(int)
			for i in get_objects():
				self._beforeLeakTest[type(i)] += 1
		if keyCode == wx.WXK_F5 and wx.GetKeyState(wx.WXK_SHIFT):
			from collections import defaultdict
			from gc import get_objects
			self._afterLeakTest = defaultdict(int)
			for i in get_objects():
				self._afterLeakTest[type(i)] += 1
			for k in self._afterLeakTest:
				if self._afterLeakTest[k]-self._beforeLeakTest[k]:
					print k, self._afterLeakTest[k], self._beforeLeakTest[k], self._afterLeakTest[k] - self._beforeLeakTest[k]

	def ShaderUpdate(self, v, f):
		s = opengl.GLShader(v, f)
		if s.isValid():
			self._objectLoadShader.release()
			self._objectLoadShader = s
			for obj in self._scene.objects():
				obj._loadAnim = openglGui.animation(self, 1, 0, 1.5)
			self.QueueRefresh()

	def OnMouseDown(self,e):
		self._mouseX = e.GetX()
		self._mouseY = e.GetY()
		self._mouseClick3DPos = self._mouse3Dpos
		self._mouseClickFocus = self._focusObj
		if e.ButtonDClick():
			self._mouseState = 'doubleClick'
		else:
			self._mouseState = 'dragOrClick'
		p0, p1 = self.getMouseRay(self._mouseX, self._mouseY)
		p0 -= self.getObjectCenterPos() - self._viewTarget
		p1 -= self.getObjectCenterPos() - self._viewTarget
		if self.tool.OnDragStart(p0, p1):
			self._mouseState = 'tool'
		if self._mouseState == 'dragOrClick':
			if e.GetButton() == 1:
				if self._focusObj is not None:
					self._selectObject(self._focusObj, False)
					self.QueueRefresh()

	def OnMouseUp(self, e):
		if e.LeftIsDown() or e.MiddleIsDown() or e.RightIsDown():
			return
		if self._mouseState == 'dragOrClick':
			if e.GetButton() == 1:
				self._selectObject(self._focusObj)
			if e.GetButton() == 3:
					menu = wx.Menu()
					if self._focusObj is not None:
						self.Bind(wx.EVT_MENU, lambda e: self._deleteObject(self._focusObj), menu.Append(-1, _("Delete object")))
						self.Bind(wx.EVT_MENU, self.OnCenter, menu.Append(-1, _("Center on platform")))
						self.Bind(wx.EVT_MENU, self.OnMultiply, menu.Append(-1, _("Multiply object")))
						self.Bind(wx.EVT_MENU, self.OnSplitObject, menu.Append(-1, _("Split object into parts")))
					if ((self._selectedObj != self._focusObj and self._focusObj is not None and self._selectedObj is not None) or len(self._scene.objects()) == 2) and int(profile.getMachineSetting('extruder_amount')) > 1:
						self.Bind(wx.EVT_MENU, self.OnMergeObjects, menu.Append(-1, _("Dual extrusion merge")))
					if len(self._scene.objects()) > 0:
						self.Bind(wx.EVT_MENU, self.OnDeleteAll, menu.Append(-1, _("Delete all objects")))
					if menu.MenuItemCount > 0:
						self.PopupMenu(menu)
					menu.Destroy()
		elif self._mouseState == 'dragObject' and self._selectedObj is not None:
			self._scene.pushFree()
			self.sceneUpdated()
		elif self._mouseState == 'tool':
			if self.tempMatrix is not None and self._selectedObj is not None:
				self._selectedObj.applyMatrix(self.tempMatrix)
				self._scene.pushFree()
				self._selectObject(self._selectedObj)
			self.tempMatrix = None
			self.tool.OnDragEnd()
			self.sceneUpdated()
		self._mouseState = None

	def OnMouseMotion(self,e):
		p0, p1 = self.getMouseRay(e.GetX(), e.GetY())
		p0 -= self.getObjectCenterPos() - self._viewTarget
		p1 -= self.getObjectCenterPos() - self._viewTarget

		if e.Dragging() and self._mouseState is not None:
			if self._mouseState == 'tool':
				self.tool.OnDrag(p0, p1)
			elif not e.LeftIsDown() and e.RightIsDown():
				self._mouseState = 'drag'
				if wx.GetKeyState(wx.WXK_SHIFT):
					a = math.cos(math.radians(self._yaw)) / 3.0
					b = math.sin(math.radians(self._yaw)) / 3.0
					self._viewTarget[0] += float(e.GetX() - self._mouseX) * -a
					self._viewTarget[1] += float(e.GetX() - self._mouseX) * b
					self._viewTarget[0] += float(e.GetY() - self._mouseY) * b
					self._viewTarget[1] += float(e.GetY() - self._mouseY) * a
				else:
					self._yaw += e.GetX() - self._mouseX
					self._pitch -= e.GetY() - self._mouseY
				if self._pitch > 170:
					self._pitch = 170
				if self._pitch < 10:
					self._pitch = 10
			elif (e.LeftIsDown() and e.RightIsDown()) or e.MiddleIsDown():
				self._mouseState = 'drag'
				self._zoom += e.GetY() - self._mouseY
				if self._zoom < 1:
					self._zoom = 1
				if self._zoom > numpy.max(self._machineSize) * 3:
					self._zoom = numpy.max(self._machineSize) * 3
			elif e.LeftIsDown() and self._selectedObj is not None and self._selectedObj == self._mouseClickFocus:
				self._mouseState = 'dragObject'
				z = max(0, self._mouseClick3DPos[2])
				p0, p1 = self.getMouseRay(self._mouseX, self._mouseY)
				p2, p3 = self.getMouseRay(e.GetX(), e.GetY())
				p0[2] -= z
				p1[2] -= z
				p2[2] -= z
				p3[2] -= z
				cursorZ0 = p0 - (p1 - p0) * (p0[2] / (p1[2] - p0[2]))
				cursorZ1 = p2 - (p3 - p2) * (p2[2] / (p3[2] - p2[2]))
				diff = cursorZ1 - cursorZ0
				self._selectedObj.setPosition(self._selectedObj.getPosition() + diff[0:2])
		if not e.Dragging() or self._mouseState != 'tool':
			self.tool.OnMouseMove(p0, p1)

		self._mouseX = e.GetX()
		self._mouseY = e.GetY()

	def OnMouseWheel(self, e):
		delta = float(e.GetWheelRotation()) / float(e.GetWheelDelta())
		delta = max(min(delta,4),-4)
		self._zoom *= 1.0 - delta / 10.0
		if self._zoom < 1.0:
			self._zoom = 1.0
		if self._zoom > numpy.max(self._machineSize) * 3:
			self._zoom = numpy.max(self._machineSize) * 3
		self.Refresh()

	def OnMouseLeave(self, e):
		#self._mouseX = -1
		pass

	def getMouseRay(self, x, y):
		if self._viewport is None:
			return numpy.array([0,0,0],numpy.float32), numpy.array([0,0,1],numpy.float32)
		p0 = opengl.unproject(x, self._viewport[1] + self._viewport[3] - y, 0, self._modelMatrix, self._projMatrix, self._viewport)
		p1 = opengl.unproject(x, self._viewport[1] + self._viewport[3] - y, 1, self._modelMatrix, self._projMatrix, self._viewport)
		p0 -= self._viewTarget
		p1 -= self._viewTarget
		return p0, p1

	def _init3DView(self):
		# set viewing projection
		size = self.GetSize()
		glViewport(0, 0, size.GetWidth(), size.GetHeight())
		glLoadIdentity()

		glLightfv(GL_LIGHT0, GL_POSITION, [0.2, 0.2, 1.0, 0.0])

		glDisable(GL_RESCALE_NORMAL)
		glDisable(GL_LIGHTING)
		glDisable(GL_LIGHT0)
		glEnable(GL_DEPTH_TEST)
		glDisable(GL_CULL_FACE)
		glDisable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		glClearColor(0.8, 0.8, 0.8, 1.0)
		glClearStencil(0)
		glClearDepth(1.0)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		aspect = float(size.GetWidth()) / float(size.GetHeight())
		gluPerspective(45.0, aspect, 1.0, numpy.max(self._machineSize) * 4)

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

	def OnPaint(self,e):
		if machineCom.machineIsConnected():
			self.printButton._imageID = 6
			self.printButton._tooltip = _("Print")
		elif len(removableStorage.getPossibleSDcardDrives()) > 0:
			self.printButton._imageID = 2
			self.printButton._tooltip = _("Toolpath to SD")
		else:
			self.printButton._imageID = 3
			self.printButton._tooltip = _("Save toolpath")

		if self._animView is not None:
			self._viewTarget = self._animView.getPosition()
			if self._animView.isDone():
				self._animView = None
		if self._animZoom is not None:
			self._zoom = self._animZoom.getPosition()
			if self._animZoom.isDone():
				self._animZoom = None
		if self.viewMode == 'gcode' and self._gcode is not None:
			try:
				self._viewTarget[2] = self._gcode.layerList[self.layerSelect.getValue()][-1]['points'][0][2]
			except:
				pass
		if self._objectShader is None:
			if opengl.hasShaderSupport():
				self._objectShader = opengl.GLShader("""
varying float light_amount;

void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount += 0.2;
}
				""","""
varying float light_amount;

void main(void)
{
	gl_FragColor = vec4(gl_Color.xyz * light_amount, gl_Color[3]);
}
				""")
				self._objectOverhangShader = opengl.GLShader("""
uniform float cosAngle;
uniform mat3 rotMatrix;
varying float light_amount;

void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount += 0.2;
	if (normalize(rotMatrix * gl_Normal).z < -cosAngle)
	{
		light_amount = -10.0;
	}
}
				""","""
varying float light_amount;

void main(void)
{
	if (light_amount == -10.0)
	{
		gl_FragColor = vec4(1.0, 0.0, 0.0, gl_Color[3]);
	}else{
		gl_FragColor = vec4(gl_Color.xyz * light_amount, gl_Color[3]);
	}
}
				""")
				self._objectLoadShader = opengl.GLShader("""
uniform float intensity;
uniform float scale;
varying float light_amount;

void main(void)
{
	vec4 tmp = gl_Vertex;
    tmp.x += sin(tmp.z/5.0+intensity*30.0) * scale * intensity;
    tmp.y += sin(tmp.z/3.0+intensity*40.0) * scale * intensity;
    gl_Position = gl_ModelViewProjectionMatrix * tmp;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount += 0.2;
}
			""","""
uniform float intensity;
varying float light_amount;

void main(void)
{
	gl_FragColor = vec4(gl_Color.xyz * light_amount, 1.0-intensity);
}
				""")
			if self._objectShader == None or not self._objectShader.isValid():
				self._objectShader = opengl.GLFakeShader()
				self._objectOverhangShader = opengl.GLFakeShader()
				self._objectLoadShader = None
		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		self._viewport = glGetIntegerv(GL_VIEWPORT)
		self._modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
		self._projMatrix = glGetDoublev(GL_PROJECTION_MATRIX)

		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

		if self.viewMode != 'gcode':
			for n in xrange(0, len(self._scene.objects())):
				obj = self._scene.objects()[n]
				glColor4ub((n >> 16) & 0xFF, (n >> 8) & 0xFF, (n >> 0) & 0xFF, 0xFF)
				self._renderObject(obj)

		if self._mouseX > -1:
			glFlush()
			n = glReadPixels(self._mouseX, self.GetSize().GetHeight() - 1 - self._mouseY, 1, 1, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8
			if n < len(self._scene.objects()):
				self._focusObj = self._scene.objects()[n]
			else:
				self._focusObj = None
			f = glReadPixels(self._mouseX, self.GetSize().GetHeight() - 1 - self._mouseY, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[0][0]
			#self.GetTopLevelParent().SetTitle(hex(n) + " " + str(f))
			self._mouse3Dpos = opengl.unproject(self._mouseX, self._viewport[1] + self._viewport[3] - self._mouseY, f, self._modelMatrix, self._projMatrix, self._viewport)
			self._mouse3Dpos -= self._viewTarget

		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		if self.viewMode == 'gcode':
			if self._gcode is not None and self._gcode.layerList is None:
				self._gcodeLoadThread = threading.Thread(target=self._loadGCode)
				self._gcodeLoadThread.daemon = True
				self._gcodeLoadThread.start()
			if self._gcode is not None and self._gcode.layerList is not None:
				glPushMatrix()
				if profile.getMachineSetting('machine_center_is_zero') != 'True':
					glTranslate(-self._machineSize[0] / 2, -self._machineSize[1] / 2, 0)
				t = time.time()
				drawUpTill = min(len(self._gcode.layerList), self.layerSelect.getValue() + 1)
				for n in xrange(0, drawUpTill):
					c = 1.0 - float(drawUpTill - n) / 15
					c = max(0.3, c)
					if len(self._gcodeVBOs) < n + 1:
						self._gcodeVBOs.append(self._generateGCodeVBOs(self._gcode.layerList[n]))
						if time.time() - t > 0.5:
							self.QueueRefresh()
							break
					#['WALL-OUTER', 'WALL-INNER', 'FILL', 'SUPPORT', 'SKIRT']
					if n == drawUpTill - 1:
						if len(self._gcodeVBOs[n]) < 9:
							self._gcodeVBOs[n] += self._generateGCodeVBOs2(self._gcode.layerList[n])
						glColor3f(c, 0, 0)
						self._gcodeVBOs[n][8].render(GL_QUADS)
						glColor3f(c/2, 0, c)
						self._gcodeVBOs[n][9].render(GL_QUADS)
						glColor3f(0, c, c/2)
						self._gcodeVBOs[n][10].render(GL_QUADS)
						glColor3f(c, 0, 0)
						self._gcodeVBOs[n][11].render(GL_QUADS)

						glColor3f(0, c, 0)
						self._gcodeVBOs[n][12].render(GL_QUADS)
						glColor3f(c/2, c/2, 0.0)
						self._gcodeVBOs[n][13].render(GL_QUADS)
						glColor3f(0, c, c)
						self._gcodeVBOs[n][14].render(GL_QUADS)
						self._gcodeVBOs[n][15].render(GL_QUADS)
						glColor3f(0, 0, c)
						self._gcodeVBOs[n][16].render(GL_LINES)
					else:
						glColor3f(c, 0, 0)
						self._gcodeVBOs[n][0].render(GL_LINES)
						glColor3f(c/2, 0, c)
						self._gcodeVBOs[n][1].render(GL_LINES)
						glColor3f(0, c, c/2)
						self._gcodeVBOs[n][2].render(GL_LINES)
						glColor3f(c, 0, 0)
						self._gcodeVBOs[n][3].render(GL_LINES)

						glColor3f(0, c, 0)
						self._gcodeVBOs[n][4].render(GL_LINES)
						glColor3f(c/2, c/2, 0.0)
						self._gcodeVBOs[n][5].render(GL_LINES)
						glColor3f(0, c, c)
						self._gcodeVBOs[n][6].render(GL_LINES)
						self._gcodeVBOs[n][7].render(GL_LINES)
				glPopMatrix()
		else:
			glStencilFunc(GL_ALWAYS, 1, 1)
			glStencilOp(GL_INCR, GL_INCR, GL_INCR)

			if self.viewMode == 'overhang':
				self._objectOverhangShader.bind()
				self._objectOverhangShader.setUniform('cosAngle', math.cos(math.radians(90 - 60)))
			else:
				self._objectShader.bind()
			for obj in self._scene.objects():
				if obj._loadAnim is not None:
					if obj._loadAnim.isDone():
						obj._loadAnim = None
					else:
						continue
				brightness = 1.0
				if self._focusObj == obj:
					brightness = 1.2
				elif self._focusObj is not None or self._selectedObj is not None and obj != self._selectedObj:
					brightness = 0.8

				if self._selectedObj == obj or self._selectedObj is None:
					#If we want transparent, then first render a solid black model to remove the printer size lines.
					if self.viewMode == 'transparent':
						glColor4f(0, 0, 0, 0)
						self._renderObject(obj)
						glEnable(GL_BLEND)
						glBlendFunc(GL_ONE, GL_ONE)
						glDisable(GL_DEPTH_TEST)
						brightness *= 0.5
					if self.viewMode == 'xray':
						glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
					glStencilOp(GL_INCR, GL_INCR, GL_INCR)
					glEnable(GL_STENCIL_TEST)

				if self.viewMode == 'overhang':
					if self._selectedObj == obj and self.tempMatrix is not None:
						self._objectOverhangShader.setUniform('rotMatrix', obj.getMatrix() * self.tempMatrix)
					else:
						self._objectOverhangShader.setUniform('rotMatrix', obj.getMatrix())

				if not self._scene.checkPlatform(obj):
					glColor4f(0.5 * brightness, 0.5 * brightness, 0.5 * brightness, 0.8 * brightness)
					self._renderObject(obj)
				else:
					self._renderObject(obj, brightness)
				glDisable(GL_STENCIL_TEST)
				glDisable(GL_BLEND)
				glEnable(GL_DEPTH_TEST)
				glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

			if self.viewMode == 'xray':
				glPushMatrix()
				glLoadIdentity()
				glEnable(GL_STENCIL_TEST)
				glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
				glDisable(GL_DEPTH_TEST)
				for i in xrange(2, 15, 2):
					glStencilFunc(GL_EQUAL, i, 0xFF)
					glColor(float(i)/10, float(i)/10, float(i)/5)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-10)
					glVertex3f( 1000,-1000,-10)
					glVertex3f( 1000, 1000,-10)
					glVertex3f(-1000, 1000,-10)
					glEnd()
				for i in xrange(1, 15, 2):
					glStencilFunc(GL_EQUAL, i, 0xFF)
					glColor(float(i)/10, 0, 0)
					glBegin(GL_QUADS)
					glVertex3f(-1000,-1000,-10)
					glVertex3f( 1000,-1000,-10)
					glVertex3f( 1000, 1000,-10)
					glVertex3f(-1000, 1000,-10)
					glEnd()
				glPopMatrix()
				glDisable(GL_STENCIL_TEST)
				glEnable(GL_DEPTH_TEST)

			self._objectShader.unbind()

			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
			glEnable(GL_BLEND)
			if self._objectLoadShader is not None:
				self._objectLoadShader.bind()
				glColor4f(0.2, 0.6, 1.0, 1.0)
				for obj in self._scene.objects():
					if obj._loadAnim is None:
						continue
					self._objectLoadShader.setUniform('intensity', obj._loadAnim.getPosition())
					self._objectLoadShader.setUniform('scale', obj.getBoundaryCircle() / 10)
					self._renderObject(obj)
				self._objectLoadShader.unbind()
				glDisable(GL_BLEND)

		self._drawMachine()

		if self._usbPrintMonitor.getState() == 'PRINTING' and self._usbPrintMonitor.getID() == self._slicer.getID():
			glEnable(GL_BLEND)
			z = self._usbPrintMonitor.getZ()
			size = self._machineSize
			glColor4ub(255,255,0,128)
			glBegin(GL_QUADS)
			glVertex3f(-size[0]/2,-size[1]/2, z)
			glVertex3f( size[0]/2,-size[1]/2, z)
			glVertex3f( size[0]/2, size[1]/2, z)
			glVertex3f(-size[0]/2, size[1]/2, z)
			glEnd()

		if self.viewMode == 'gcode':
			if self._gcodeLoadThread is not None and self._gcodeLoadThread.isAlive():
				glDisable(GL_DEPTH_TEST)
				glPushMatrix()
				glLoadIdentity()
				glTranslate(0,-4,-10)
				glColor4ub(60,60,60,255)
				opengl.glDrawStringCenter(_("Loading toolpath for visualization..."))
				glPopMatrix()
		else:
			#Draw the object box-shadow, so you can see where it will collide with other objects.
			if self._selectedObj is not None and len(self._scene.objects()) > 1:
				size = self._selectedObj.getSize()[0:2] / 2 + self._scene.getObjectExtend()
				glPushMatrix()
				glTranslatef(self._selectedObj.getPosition()[0], self._selectedObj.getPosition()[1], 0)
				glEnable(GL_BLEND)
				glEnable(GL_CULL_FACE)
				glColor4f(0,0,0,0.12)
				glBegin(GL_QUADS)
				glVertex3f(-size[0],  size[1], 0.1)
				glVertex3f(-size[0], -size[1], 0.1)
				glVertex3f( size[0], -size[1], 0.1)
				glVertex3f( size[0],  size[1], 0.1)
				glEnd()
				glDisable(GL_CULL_FACE)
				glPopMatrix()

			#Draw the outline of the selected object, on top of everything else except the GUI.
			if self._selectedObj is not None and self._selectedObj._loadAnim is None:
				glDisable(GL_DEPTH_TEST)
				glEnable(GL_CULL_FACE)
				glEnable(GL_STENCIL_TEST)
				glDisable(GL_BLEND)
				glStencilFunc(GL_EQUAL, 0, 255)

				glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
				glLineWidth(2)
				glColor4f(1,1,1,0.5)
				self._renderObject(self._selectedObj)
				glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

				glViewport(0, 0, self.GetSize().GetWidth(), self.GetSize().GetHeight())
				glDisable(GL_STENCIL_TEST)
				glDisable(GL_CULL_FACE)
				glEnable(GL_DEPTH_TEST)

			if self._selectedObj is not None:
				glPushMatrix()
				pos = self.getObjectCenterPos()
				glTranslate(pos[0], pos[1], pos[2])
				self.tool.OnDraw()
				glPopMatrix()
		if self.viewMode == 'overhang' and not opengl.hasShaderSupport():
			glDisable(GL_DEPTH_TEST)
			glPushMatrix()
			glLoadIdentity()
			glTranslate(0,-4,-10)
			glColor4ub(60,60,60,255)
			opengl.glDrawStringCenter(_("Overhang view not working due to lack of OpenGL shaders support."))
			glPopMatrix()

	def _renderObject(self, obj, brightness = False, addSink = True):
		glPushMatrix()
		if addSink:
			glTranslate(obj.getPosition()[0], obj.getPosition()[1], obj.getSize()[2] / 2 - profile.getProfileSettingFloat('object_sink'))
		else:
			glTranslate(obj.getPosition()[0], obj.getPosition()[1], obj.getSize()[2] / 2)

		if self.tempMatrix is not None and obj == self._selectedObj:
			tempMatrix = opengl.convert3x3MatrixTo4x4(self.tempMatrix)
			glMultMatrixf(tempMatrix)

		offset = obj.getDrawOffset()
		glTranslate(-offset[0], -offset[1], -offset[2] - obj.getSize()[2] / 2)

		tempMatrix = opengl.convert3x3MatrixTo4x4(obj.getMatrix())
		glMultMatrixf(tempMatrix)

		n = 0
		for m in obj._meshList:
			if m.vbo is None:
				m.vbo = opengl.GLVBO(m.vertexes, m.normal)
			if brightness:
				glColor4fv(map(lambda n: n * brightness, self._objColors[n]))
				n += 1
			m.vbo.render()
		glPopMatrix()

	def _drawMachine(self):
		glEnable(GL_CULL_FACE)
		glEnable(GL_BLEND)

		size = [profile.getMachineSettingFloat('machine_width'), profile.getMachineSettingFloat('machine_depth'), profile.getMachineSettingFloat('machine_height')]

		machine = profile.getMachineSetting('machine_type')
		if profile.getMachineSetting('machine_type').startswith('ultimaker'):
			if machine not in self._platformMesh:
				meshes = meshLoader.loadMeshes(resources.getPathForMesh(machine + '_platform.stl'))
				if len(meshes) > 0:
					self._platformMesh[machine] = meshes[0]
				else:
					self._platformMesh[machine] = None
				if machine == 'ultimaker2':
					self._platformMesh[machine]._drawOffset = numpy.array([0,-37,145], numpy.float32)
				else:
					self._platformMesh[machine]._drawOffset = numpy.array([0,0,2.5], numpy.float32)
			glColor4f(1,1,1,0.5)
			self._objectShader.bind()
			self._renderObject(self._platformMesh[machine], False, False)
			self._objectShader.unbind()

			#For the Ultimaker 2 render the texture on the back plate to show the Ultimaker2 text.
			if machine == 'ultimaker2':
				if not hasattr(self._platformMesh[machine], 'texture'):
					self._platformMesh[machine].texture = opengl.loadGLTexture('Ultimaker2backplate.png')
				glBindTexture(GL_TEXTURE_2D, self._platformMesh[machine].texture)
				glEnable(GL_TEXTURE_2D)
				glPushMatrix()
				glColor4f(1,1,1,1)

				glTranslate(0,150,-5)
				h = 50
				d = 8
				w = 100
				glEnable(GL_BLEND)
				glBlendFunc(GL_DST_COLOR, GL_ZERO)
				glBegin(GL_QUADS)
				glTexCoord2f(1, 0)
				glVertex3f( w, 0, h)
				glTexCoord2f(0, 0)
				glVertex3f(-w, 0, h)
				glTexCoord2f(0, 1)
				glVertex3f(-w, 0, 0)
				glTexCoord2f(1, 1)
				glVertex3f( w, 0, 0)

				glTexCoord2f(1, 0)
				glVertex3f(-w, d, h)
				glTexCoord2f(0, 0)
				glVertex3f( w, d, h)
				glTexCoord2f(0, 1)
				glVertex3f( w, d, 0)
				glTexCoord2f(1, 1)
				glVertex3f(-w, d, 0)
				glEnd()
				glDisable(GL_TEXTURE_2D)
				glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
				glPopMatrix()
		else:
			glColor4f(0,0,0,1)
			glLineWidth(3)
			glBegin(GL_LINES)
			glVertex3f(-size[0] / 2, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2, -size[1] / 2, 10)
			glVertex3f(-size[0] / 2, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2+10, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2, -size[1] / 2, 0)
			glVertex3f(-size[0] / 2, -size[1] / 2+10, 0)
			glEnd()

		v0 = [ size[0] / 2, size[1] / 2, size[2]]
		v1 = [ size[0] / 2,-size[1] / 2, size[2]]
		v2 = [-size[0] / 2, size[1] / 2, size[2]]
		v3 = [-size[0] / 2,-size[1] / 2, size[2]]
		v4 = [ size[0] / 2, size[1] / 2, 0]
		v5 = [ size[0] / 2,-size[1] / 2, 0]
		v6 = [-size[0] / 2, size[1] / 2, 0]
		v7 = [-size[0] / 2,-size[1] / 2, 0]

		vList = [v0,v1,v3,v2, v1,v0,v4,v5, v2,v3,v7,v6, v0,v2,v6,v4, v3,v1,v5,v7]
		glEnableClientState(GL_VERTEX_ARRAY)
		glVertexPointer(3, GL_FLOAT, 3*4, vList)

		glColor4ub(5, 171, 231, 64)
		glDrawArrays(GL_QUADS, 0, 4)
		glColor4ub(5, 171, 231, 96)
		glDrawArrays(GL_QUADS, 4, 8)
		glColor4ub(5, 171, 231, 128)
		glDrawArrays(GL_QUADS, 12, 8)
		glDisableClientState(GL_VERTEX_ARRAY)

		sx = self._machineSize[0]
		sy = self._machineSize[1]
		for x in xrange(-int(sx/20)-1, int(sx / 20) + 1):
			for y in xrange(-int(sx/20)-1, int(sy / 20) + 1):
				x1 = x * 10
				x2 = x1 + 10
				y1 = y * 10
				y2 = y1 + 10
				x1 = max(min(x1, sx/2), -sx/2)
				y1 = max(min(y1, sy/2), -sy/2)
				x2 = max(min(x2, sx/2), -sx/2)
				y2 = max(min(y2, sy/2), -sy/2)
				if (x & 1) == (y & 1):
					glColor4ub(5, 171, 231, 127)
				else:
					glColor4ub(5 * 8 / 10, 171 * 8 / 10, 231 * 8 / 10, 128)
				glBegin(GL_QUADS)
				glVertex3f(x1, y1, -0.02)
				glVertex3f(x2, y1, -0.02)
				glVertex3f(x2, y2, -0.02)
				glVertex3f(x1, y2, -0.02)
				glEnd()

		glDisable(GL_BLEND)
		glDisable(GL_CULL_FACE)

	def _generateGCodeVBOs(self, layer):
		ret = []
		for extrudeType in ['WALL-OUTER:0', 'WALL-OUTER:1', 'WALL-OUTER:2', 'WALL-OUTER:3', 'WALL-INNER', 'FILL', 'SUPPORT', 'SKIRT']:
			if ':' in extrudeType:
				extruder = int(extrudeType[extrudeType.find(':')+1:])
				extrudeType = extrudeType[0:extrudeType.find(':')]
			else:
				extruder = None
			pointList = numpy.zeros((0,3), numpy.float32)
			for path in layer:
				if path['type'] == 'extrude' and path['pathType'] == extrudeType and (extruder is None or path['extruder'] == extruder):
					a = path['points']
					a = numpy.concatenate((a[:-1], a[1:]), 1)
					a = a.reshape((len(a) * 2, 3))
					pointList = numpy.concatenate((pointList, a))
			ret.append(opengl.GLVBO(pointList))
		return ret

	def _generateGCodeVBOs2(self, layer):
		filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
		filamentArea = math.pi * filamentRadius * filamentRadius
		useFilamentArea = profile.getMachineSetting('gcode_flavor') == 'UltiGCode'

		ret = []
		for extrudeType in ['WALL-OUTER:0', 'WALL-OUTER:1', 'WALL-OUTER:2', 'WALL-OUTER:3', 'WALL-INNER', 'FILL', 'SUPPORT', 'SKIRT']:
			if ':' in extrudeType:
				extruder = int(extrudeType[extrudeType.find(':')+1:])
				extrudeType = extrudeType[0:extrudeType.find(':')]
			else:
				extruder = None
			pointList = numpy.zeros((0,3), numpy.float32)
			for path in layer:
				if path['type'] == 'extrude' and path['pathType'] == extrudeType and (extruder is None or path['extruder'] == extruder):
					a = path['points']
					if extrudeType == 'FILL':
						a[:,2] += 0.01

					normal = a[1:] - a[:-1]
					lens = numpy.sqrt(normal[:,0]**2 + normal[:,1]**2)
					normal[:,0], normal[:,1] = -normal[:,1] / lens, normal[:,0] / lens
					normal[:,2] /= lens

					ePerDist = path['extrusion'][1:] / lens
					if useFilamentArea:
						lineWidth = ePerDist / path['layerThickness'] / 2.0
					else:
						lineWidth = ePerDist * (filamentArea / path['layerThickness'] / 2)

					normal[:,0] *= lineWidth
					normal[:,1] *= lineWidth

					b = numpy.zeros((len(a)-1, 0), numpy.float32)
					b = numpy.concatenate((b, a[1:] + normal), 1)
					b = numpy.concatenate((b, a[1:] - normal), 1)
					b = numpy.concatenate((b, a[:-1] - normal), 1)
					b = numpy.concatenate((b, a[:-1] + normal), 1)
					b = b.reshape((len(b) * 4, 3))

					if len(a) > 2:
						normal2 = normal[:-1] + normal[1:]
						lens2 = numpy.sqrt(normal2[:,0]**2 + normal2[:,1]**2)
						normal2[:,0] /= lens2
						normal2[:,1] /= lens2
						normal2[:,0] *= lineWidth[:-1]
						normal2[:,1] *= lineWidth[:-1]

						c = numpy.zeros((len(a)-2, 0), numpy.float32)
						c = numpy.concatenate((c, a[1:-1]), 1)
						c = numpy.concatenate((c, a[1:-1]+normal[1:]), 1)
						c = numpy.concatenate((c, a[1:-1]+normal2), 1)
						c = numpy.concatenate((c, a[1:-1]+normal[:-1]), 1)

						c = numpy.concatenate((c, a[1:-1]), 1)
						c = numpy.concatenate((c, a[1:-1]-normal[1:]), 1)
						c = numpy.concatenate((c, a[1:-1]-normal2), 1)
						c = numpy.concatenate((c, a[1:-1]-normal[:-1]), 1)

						c = c.reshape((len(c) * 8, 3))

						pointList = numpy.concatenate((pointList, b, c))
					else:
						pointList = numpy.concatenate((pointList, b))
			ret.append(opengl.GLVBO(pointList))

		pointList = numpy.zeros((0,3), numpy.float32)
		for path in layer:
			if path['type'] == 'move':
				a = path['points'] + numpy.array([0,0,0.01], numpy.float32)
				a = numpy.concatenate((a[:-1], a[1:]), 1)
				a = a.reshape((len(a) * 2, 3))
				pointList = numpy.concatenate((pointList, a))
			if path['type'] == 'retract':
				a = path['points'] + numpy.array([0,0,0.01], numpy.float32)
				a = numpy.concatenate((a[:-1], a[1:] + numpy.array([0,0,1], numpy.float32)), 1)
				a = a.reshape((len(a) * 2, 3))
				pointList = numpy.concatenate((pointList, a))
		ret.append(opengl.GLVBO(pointList))

		return ret

	def getObjectCenterPos(self):
		if self._selectedObj is None:
			return [0.0, 0.0, 0.0]
		pos = self._selectedObj.getPosition()
		size = self._selectedObj.getSize()
		return [pos[0], pos[1], size[2]/2 - profile.getProfileSettingFloat('object_sink')]

	def getObjectBoundaryCircle(self):
		if self._selectedObj is None:
			return 0.0
		return self._selectedObj.getBoundaryCircle()

	def getObjectSize(self):
		if self._selectedObj is None:
			return [0.0, 0.0, 0.0]
		return self._selectedObj.getSize()

	def getObjectMatrix(self):
		if self._selectedObj is None:
			return numpy.matrix([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
		return self._selectedObj.getMatrix()

class shaderEditor(wx.Dialog):
	def __init__(self, parent, callback, v, f):
		super(shaderEditor, self).__init__(parent, title="Shader editor", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self._callback = callback
		s = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(s)
		self._vertex = wx.TextCtrl(self, -1, v, style=wx.TE_MULTILINE)
		self._fragment = wx.TextCtrl(self, -1, f, style=wx.TE_MULTILINE)
		s.Add(self._vertex, 1, flag=wx.EXPAND)
		s.Add(self._fragment, 1, flag=wx.EXPAND)

		self._vertex.Bind(wx.EVT_TEXT, self.OnText, self._vertex)
		self._fragment.Bind(wx.EVT_TEXT, self.OnText, self._fragment)

		self.SetPosition(self.GetParent().GetPosition())
		self.SetSize((self.GetSize().GetWidth(), self.GetParent().GetSize().GetHeight()))
		self.Show()

	def OnText(self, e):
		self._callback(self._vertex.GetValue(), self._fragment.GetValue())
