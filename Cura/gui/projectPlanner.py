from __future__ import absolute_import

import wx
import os
import threading
import time
import re
import shutil
import ConfigParser
import numpy

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.gui.util import opengl
from Cura.gui.util import toolbarUtil
from Cura.gui import configBase
from Cura.gui import printWindow
from Cura.gui.util import dropTarget
from Cura.gui.util import taskbar
from Cura.gui.util import previewTools
from Cura.gui.util import openglGui
from Cura.util import validators
from Cura.util import profile
from Cura.util import util3d
from Cura.util import meshLoader
from Cura.util.meshLoaders import stl
from Cura.util import mesh
from Cura.util import sliceRun
from Cura.util import gcodeInterpreter
from Cura.util import explorer

class Action(object):
	pass

class ProjectObject(object):
	def __init__(self, parent, filename):
		super(ProjectObject, self).__init__()

		self.mesh = meshLoader.loadMesh(filename)

		self.parent = parent
		self.filename = filename
		self.matrix = numpy.matrix([[1,0,0],[0,1,0],[0,0,1]], numpy.float64)
		self.profile = None
		
		self.modelDisplayList = None
		self.modelDirty = True

		self.centerX = self.getSize()[0]/2 + 5
		self.centerY = self.getSize()[1]/2 + 5

		self.updateMatrix()

	def isSameExceptForPosition(self, other):
		if self.filename != other.filename:
			return False
		if self.matrix != other.matrix:
			return False
		if self.profile != other.profile:
			return False
		return True

	def updateMatrix(self):
		self.mesh.matrix = self.matrix
		self.mesh.processMatrix()

	def getMinimum(self):
		return self.mesh.getMinimum()
	def getMaximum(self):
		return self.mesh.getMaximum()
	def getSize(self):
		return self.mesh.getSize()
	def getBoundaryCircle(self):
		return self.mesh.bounderyCircleSize
	
	def clone(self):
		p = ProjectObject(self.parent, self.filename)

		p.centerX = self.centerX + 5
		p.centerY = self.centerY + 5
		
		p.filename = self.filename
		p.matrix = self.matrix.copy()
		p.profile = self.profile
		
		p.updateMatrix()
		
		return p
	
	def clampXY(self):
		size = self.getSize()
		if self.centerX < size[0] / 2:
			self.centerX = size[0] / 2
		if self.centerY < size[1] / 2:
			self.centerY = size[1] / 2
		if self.centerX > self.parent.machineSize[0] - size[0] / 2:
			self.centerX = self.parent.machineSize[0] - size[0] / 2
		if self.centerY > self.parent.machineSize[1] - size[1] / 2:
			self.centerY = self.parent.machineSize[1] - size[1] / 2

class projectPlanner(wx.Frame):
	"Main user interface window"
	def __init__(self):
		super(projectPlanner, self).__init__(None, title='Cura - Project Planner')
		
		wx.EVT_CLOSE(self, self.OnClose)
		self.panel = wx.Panel(self, -1)
		self.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.GetSizer().Add(self.panel, 1, flag=wx.EXPAND)

		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles, meshLoader.supportedExtensions()))
		
		self.list = []
		self.selection = None
		self.printMode = 0
		self.alwaysAutoPlace = profile.getPreference('planner_always_autoplace') == 'True'

		self.machineSize = numpy.array([profile.getPreferenceFloat('machine_width'), profile.getPreferenceFloat('machine_depth'), profile.getPreferenceFloat('machine_height')])
		self.headSizeMin = numpy.array([profile.getPreferenceFloat('extruder_head_size_min_x'), profile.getPreferenceFloat('extruder_head_size_min_y'),0])
		self.headSizeMax = numpy.array([profile.getPreferenceFloat('extruder_head_size_max_x'), profile.getPreferenceFloat('extruder_head_size_max_y'),0])

		self.extruderOffset = [
			numpy.array([0,0,0]),
			numpy.array([profile.getPreferenceFloat('extruder_offset_x1'), profile.getPreferenceFloat('extruder_offset_y1'), 0]),
			numpy.array([profile.getPreferenceFloat('extruder_offset_x2'), profile.getPreferenceFloat('extruder_offset_y2'), 0]),
			numpy.array([profile.getPreferenceFloat('extruder_offset_x3'), profile.getPreferenceFloat('extruder_offset_y3'), 0])]

		self.toolbar = toolbarUtil.Toolbar(self.panel)

		toolbarUtil.NormalButton(self.toolbar, self.OnLoadProject, 'open.png', 'Open project')
		toolbarUtil.NormalButton(self.toolbar, self.OnSaveProject, 'save.png', 'Save project')
		self.toolbar.AddSeparator()
		group = []
		toolbarUtil.RadioButton(self.toolbar, group, 'object-3d-on.png', 'object-3d-off.png', '3D view', callback=self.On3DClick).SetValue(self.alwaysAutoPlace)
		toolbarUtil.RadioButton(self.toolbar, group, 'object-top-on.png', 'object-top-off.png', 'Topdown view', callback=self.OnTopClick).SetValue(not self.alwaysAutoPlace)
		self.toolbar.AddSeparator()
		toolbarUtil.NormalButton(self.toolbar, self.OnPreferences, 'preferences.png', 'Project planner preferences')
		self.toolbar.AddSeparator()
		toolbarUtil.NormalButton(self.toolbar, self.OnCutMesh, 'cut-mesh.png', 'Cut a plate STL into multiple STL files, and add those files to the project.\nNote: Splitting up plates sometimes takes a few minutes.')
		toolbarUtil.NormalButton(self.toolbar, self.OnSaveCombinedSTL, 'save-combination.png', 'Save all the combined STL files into a single STL file as a plate.')
		self.toolbar.AddSeparator()
		group = []
		self.printOneAtATime = toolbarUtil.RadioButton(self.toolbar, group, 'view-normal-on.png', 'view-normal-off.png', 'Print one object at a time', callback=self.OnPrintTypeChange)
		self.printAllAtOnce = toolbarUtil.RadioButton(self.toolbar, group, 'all-at-once-on.png', 'all-at-once-off.png', 'Print all the objects at once', callback=self.OnPrintTypeChange)
		self.toolbar.AddSeparator()
		toolbarUtil.NormalButton(self.toolbar, self.OnQuit, 'exit.png', 'Close project planner')
		
		self.toolbar.Realize()

		self.toolbar2 = toolbarUtil.Toolbar(self.panel)

		toolbarUtil.NormalButton(self.toolbar2, self.OnAddModel, 'object-add.png', 'Add model')
		toolbarUtil.NormalButton(self.toolbar2, self.OnRemModel, 'object-remove.png', 'Remove model')
		self.toolbar2.AddSeparator()
		toolbarUtil.NormalButton(self.toolbar2, self.OnMoveUp, 'move-up.png', 'Move model up in print list')
		toolbarUtil.NormalButton(self.toolbar2, self.OnMoveDown, 'move-down.png', 'Move model down in print list')
		toolbarUtil.NormalButton(self.toolbar2, self.OnCopy, 'copy.png', 'Make a copy of the current selected object')
		toolbarUtil.NormalButton(self.toolbar2, self.OnSetCustomProfile, 'set-profile.png', 'Set a custom profile to be used to prepare a specific object.')
		self.toolbar2.AddSeparator()
		if not self.alwaysAutoPlace:
			toolbarUtil.NormalButton(self.toolbar2, self.OnAutoPlace, 'autoplace.png', 'Automaticly organize the objects on the platform.')
		toolbarUtil.NormalButton(self.toolbar2, self.OnSlice, 'slice.png', 'Prepare to project into a gcode file.')
		self.toolbar2.Realize()

		sizer = wx.GridBagSizer(2,2)
		self.panel.SetSizer(sizer)
		self.glCanvas = PreviewGLCanvas(self.panel, self)
		self.listbox = wx.ListBox(self.panel, -1, choices=[])
		self.addButton = wx.Button(self.panel, -1, "Add")
		self.remButton = wx.Button(self.panel, -1, "Remove")
		self.sliceButton = wx.Button(self.panel, -1, "Prepare")
		if not self.alwaysAutoPlace:
			self.autoPlaceButton = wx.Button(self.panel, -1, "Auto Place")
		
		sizer.Add(self.toolbar, (0,0), span=(1,1), flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
		sizer.Add(self.toolbar2, (0,1), span=(1,2), flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
		sizer.Add(self.glCanvas, (1,0), span=(5,1), flag=wx.EXPAND)
		sizer.Add(self.listbox, (1,1), span=(1,2), flag=wx.EXPAND)
		sizer.Add(self.addButton, (2,1), span=(1,1))
		sizer.Add(self.remButton, (2,2), span=(1,1))
		sizer.Add(self.sliceButton, (3,1), span=(1,1))
		if not self.alwaysAutoPlace:
			sizer.Add(self.autoPlaceButton, (3,2), span=(1,1))
		sizer.AddGrowableCol(0)
		sizer.AddGrowableRow(1)
		
		self.addButton.Bind(wx.EVT_BUTTON, self.OnAddModel)
		self.remButton.Bind(wx.EVT_BUTTON, self.OnRemModel)
		self.sliceButton.Bind(wx.EVT_BUTTON, self.OnSlice)
		if not self.alwaysAutoPlace:
			self.autoPlaceButton.Bind(wx.EVT_BUTTON, self.OnAutoPlace)
		self.listbox.Bind(wx.EVT_LISTBOX, self.OnListSelect)

		panel = wx.Panel(self.panel, -1)
		sizer.Add(panel, (5,1), span=(1,2))
		
		sizer = wx.GridBagSizer(2,2)
		panel.SetSizer(sizer)
		
		self.rotateToolButton = openglGui.glButton(self.glCanvas, 1, 'Rotate', (0,1), self.OnRotateSelect)
		self.scaleToolButton  = openglGui.glButton(self.glCanvas, 2, 'Scale', (0,2), self.OnScaleSelect)

		self.SetSize((800,600))

		self.tool = previewTools.toolInfo(self.glCanvas)

	def OnInfoSelect(self):
		self.infoToolButton.setSelected(True)
		self.rotateToolButton.setSelected(False)
		self.scaleToolButton.setSelected(False)
		self.tool = previewTools.toolInfo(self.glCanvas)
		self.glCanvas.Refresh()

	def OnRotateSelect(self):
		self.rotateToolButton.setSelected(True)
		self.scaleToolButton.setSelected(False)
		self.tool = previewTools.toolRotate(self.glCanvas)
		self.glCanvas.Refresh()

	def OnScaleSelect(self):
		self.rotateToolButton.setSelected(False)
		self.scaleToolButton.setSelected(True)
		self.tool = previewTools.toolScale(self.glCanvas)
		self.glCanvas.Refresh()

	def OnClose(self, e):
		self.Destroy()

	def OnQuit(self, e):
		self.Close()
	
	def OnPreferences(self, e):
		prefDialog = preferencesDialog(self)
		prefDialog.Centre()
		prefDialog.Show(True)
	
	def OnCutMesh(self, e):
		dlg=wx.FileDialog(self, "Open file to cut", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard(meshLoader.wildcardFilter())
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			model = meshLoader.loadMesh(filename)
			pd = wx.ProgressDialog('Splitting model.', 'Splitting model into multiple parts.', model.vertexCount, self, wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME | wx.PD_SMOOTH)
			parts = model.splitToParts(pd.Update)
			for part in parts:
				partFilename = filename[:filename.rfind('.')] + "_part%d.stl" % (parts.index(part))
				stl.saveAsSTL(part, partFilename)
				item = ProjectObject(self, partFilename)
				self.list.append(item)
				self.selection = item
				self._updateListbox()
				self.OnListSelect(None)
			pd.Destroy()
		self.glCanvas.Refresh()
		dlg.Destroy()
	
	def OnDropFiles(self, filenames):
		for filename in filenames:
			item = ProjectObject(self, filename)
			profile.putPreference('lastFile', item.filename)
			self.list.append(item)
			self.selection = item
			self._updateListbox()
		self.OnListSelect(None)
		self.glCanvas.Refresh()

	def OnPrintTypeChange(self):
		self.printMode = 0
		if self.printAllAtOnce.GetValue():
			self.printMode = 1
		if self.alwaysAutoPlace:
			self.OnAutoPlace(None)
		self.glCanvas.Refresh()
	
	def OnSaveCombinedSTL(self, e):
		dlg=wx.FileDialog(self, "Save as STL", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("STL files (*.stl)|*.stl;*.STL")
		if dlg.ShowModal() == wx.ID_OK:
			self._saveCombinedSTL(dlg.GetPath())
		dlg.Destroy()
	
	def _saveCombinedSTL(self, filename):
		totalCount = 0
		for item in self.list:
			totalCount += item.mesh.vertexCount
		output = mesh.mesh()
		output._prepareVertexCount(totalCount)
		for item in self.list:
			vMin = item.getMinimum()
			vMax = item.getMaximum()
			offset = - vMin - (vMax - vMin) / 2
			offset += numpy.array([item.centerX, item.centerY, (vMax[2] - vMin[2]) / 2])
			vertexes = (item.mesh.vertexes * item.matrix).getA() + offset
			for v in vertexes:
				output.addVertex(v[0], v[1], v[2])
		stl.saveAsSTL(output, filename)
	
	def OnSaveProject(self, e):
		dlg=wx.FileDialog(self, "Save project file", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("Project files (*.curaproject)|*.curaproject")
		if dlg.ShowModal() == wx.ID_OK:
			cp = ConfigParser.ConfigParser()
			i = 0
			for item in self.list:
				section = 'model_%d' % (i)
				cp.add_section(section)
				cp.set(section, 'filename', item.filename.encode("utf-8"))
				cp.set(section, 'centerX', str(item.centerX))
				cp.set(section, 'centerY', str(item.centerY))
				cp.set(section, 'scale', str(item.scale))
				cp.set(section, 'rotate', str(item.rotate))
				cp.set(section, 'flipX', str(item.flipX))
				cp.set(section, 'flipY', str(item.flipY))
				cp.set(section, 'flipZ', str(item.flipZ))
				cp.set(section, 'swapXZ', str(item.swapXZ))
				cp.set(section, 'swapYZ', str(item.swapYZ))
				cp.set(section, 'extruder', str(item.extruder+1))
				if item.profile != None:
					cp.set(section, 'profile', item.profile)
				i += 1
			cp.write(open(dlg.GetPath(), "w"))
		dlg.Destroy()

	def OnLoadProject(self, e):
		dlg=wx.FileDialog(self, "Open project file", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("Project files (*.curaproject)|*.curaproject")
		if dlg.ShowModal() == wx.ID_OK:
			cp = ConfigParser.ConfigParser()
			cp.read(dlg.GetPath())
			self.list = []
			i = 0
			while cp.has_section('model_%d' % (i)):
				section = 'model_%d' % (i)
				
				item = ProjectObject(self, unicode(cp.get(section, 'filename'), "utf-8"))
				item.centerX = float(cp.get(section, 'centerX'))
				item.centerY = float(cp.get(section, 'centerY'))
				item.scale = float(cp.get(section, 'scale'))
				item.rotate = float(cp.get(section, 'rotate'))
				item.flipX = cp.get(section, 'flipX') == 'True'
				item.flipY = cp.get(section, 'flipY') == 'True'
				item.flipZ = cp.get(section, 'flipZ') == 'True'
				item.swapXZ = cp.get(section, 'swapXZ') == 'True'
				item.swapYZ = cp.get(section, 'swapYZ') == 'True'
				if cp.has_option(section, 'extruder'):
					item.extuder = int(cp.get(section, 'extruder')) - 1
				if cp.has_option(section, 'profile'):
					item.profile = cp.get(section, 'profile')
				item.updateModelTransform()
				i += 1
				
				self.list.append(item)

			self.selected = self.list[0]
			self._updateListbox()			
			self.OnListSelect(None)
			self.glCanvas.Refresh()

		dlg.Destroy()

	def On3DClick(self):
		self.glCanvas.yaw = 30
		self.glCanvas.pitch = 60
		self.glCanvas.zoom = 300
		self.glCanvas.view3D = True
		self.glCanvas.Refresh()

	def OnTopClick(self):
		self.glCanvas.view3D = False
		self.glCanvas.zoom = self.machineSize[0] / 2 + 10
		self.glCanvas.offsetX = 0
		self.glCanvas.offsetY = 0
		self.glCanvas.Refresh()

	def OnListSelect(self, e):
		if self.listbox.GetSelection() == -1:
			return
		self.selection = self.list[self.listbox.GetSelection()]
		self.glCanvas.Refresh()
	
	def OnAddModel(self, e):
		dlg=wx.FileDialog(self, "Open file to print", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_MULTIPLE)
		dlg.SetWildcard(meshLoader.wildcardFilter())
		if dlg.ShowModal() == wx.ID_OK:
			for filename in dlg.GetPaths():
				item = ProjectObject(self, filename)
				profile.putPreference('lastFile', item.filename)
				self.list.append(item)
				self.selection = item
				self._updateListbox()
				self.OnListSelect(None)
		self.glCanvas.Refresh()
		dlg.Destroy()
	
	def OnRemModel(self, e):
		if self.selection is None:
			return
		self.list.remove(self.selection)
		self._updateListbox()
		self.glCanvas.Refresh()
	
	def OnMoveUp(self, e):
		if self.selection is None:
			return
		i = self.listbox.GetSelection()
		if i == 0:
			return
		self.list.remove(self.selection)
		self.list.insert(i-1, self.selection)
		self._updateListbox()
		self.glCanvas.Refresh()

	def OnMoveDown(self, e):
		if self.selection is None:
			return
		i = self.listbox.GetSelection()
		if i == len(self.list) - 1:
			return
		self.list.remove(self.selection)
		self.list.insert(i+1, self.selection)
		self._updateListbox()
		self.glCanvas.Refresh()
	
	def OnCopy(self, e):
		if self.selection is None:
			return
		
		item = self.selection.clone()
		self.list.insert(self.list.index(self.selection), item)
		self.selection = item
		
		self._updateListbox()
		self.glCanvas.Refresh()
	
	def OnSetCustomProfile(self, e):
		if self.selection is None:
			return

		dlg=wx.FileDialog(self, "Select profile", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
		dlg.SetWildcard("Profile files (*.ini)|*.ini;*.INI")
		if dlg.ShowModal() == wx.ID_OK:
			self.selection.profile = dlg.GetPath()
		else:
			self.selection.profile = None
		self._updateListbox()
		dlg.Destroy()
	
	def _updateListbox(self):
		self.listbox.Clear()
		for item in self.list:
			if item.profile is not None:
				self.listbox.AppendAndEnsureVisible(os.path.split(item.filename)[1] + " *")
			else:
				self.listbox.AppendAndEnsureVisible(os.path.split(item.filename)[1])
		if self.selection in self.list:
			self.listbox.SetSelection(self.list.index(self.selection))
		elif len(self.list) > 0:
			self.selection = self.list[0]
			self.listbox.SetSelection(0)
		else:
			self.selection = None
			self.listbox.SetSelection(-1)
		if self.alwaysAutoPlace:
			self.OnAutoPlace(None)

	def OnAutoPlace(self, e):
		bestAllowedSize = int(self.machineSize[1])
		bestArea = self._doAutoPlace(bestAllowedSize)
		for i in xrange(10, int(self.machineSize[1]), 10):
			area = self._doAutoPlace(i)
			if area < bestArea:
				bestAllowedSize = i
				bestArea = area
		self._doAutoPlace(bestAllowedSize)
		if not self.alwaysAutoPlace:
			for item in self.list:
				item.clampXY()
		self.glCanvas.Refresh()
	
	def _doAutoPlace(self, allowedSizeY):
		extraSizeMin, extraSizeMax = self.getExtraHeadSize()

		if extraSizeMin[0] > extraSizeMax[0]:
			posX = self.machineSize[0]
			dirX = -1
		else:
			posX = 0
			dirX = 1
		posY = 0
		dirY = 1
		
		minX = self.machineSize[0]
		minY = self.machineSize[1]
		maxX = 0
		maxY = 0
		for item in self.list:
			item.centerX = posX + item.getSize()[0] / 2 * dirX
			item.centerY = posY + item.getSize()[1] / 2 * dirY
			if item.centerY + item.getSize()[1] >= allowedSizeY:
				if dirX < 0:
					posX = minX - extraSizeMax[0] - 1
				else:
					posX = maxX + extraSizeMin[0] + 1
				posY = 0
				item.centerX = posX + item.getSize()[0] / 2 * dirX
				item.centerY = posY + item.getSize()[1] / 2 * dirY
			posY += item.getSize()[1]  * dirY + extraSizeMin[1] + 1
			minX = min(minX, item.centerX - item.getSize()[0] / 2)
			minY = min(minY, item.centerY - item.getSize()[1] / 2)
			maxX = max(maxX, item.centerX + item.getSize()[0] / 2)
			maxY = max(maxY, item.centerY + item.getSize()[1] / 2)
		
		for item in self.list:
			if dirX < 0:
				item.centerX -= minX / 2
			else:
				item.centerX += (self.machineSize[0] - maxX) / 2
			item.centerY += (self.machineSize[1] - maxY) / 2
		
		if minX < 0 or maxX > self.machineSize[0]:
			return ((maxX - minX) + (maxY - minY)) * 100
		
		return (maxX - minX) + (maxY - minY)

	def OnSlice(self, e):
		dlg=wx.FileDialog(self, "Save project gcode file", os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_SAVE)
		dlg.SetWildcard("GCode file (*.gcode)|*.gcode")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		resultFilename = dlg.GetPath()
		dlg.Destroy()

		put = profile.setTempOverride
		oldProfile = profile.getGlobalProfileString()
		
		if self.printMode == 0:
			fileList = []
			positionList = []
			for item in self.list:
				fileList.append(item.filename)
				if profile.getPreference('machine_center_is_zero') == 'True':
					pos = [item.centerX - self.machineSize[0] / 2, item.centerY - self.machineSize[1] / 2]
				else:
					pos = [item.centerX, item.centerY]
				positionList.append(pos + item.matrix.getA().flatten().tolist())
			print positionList
			sliceCommand = sliceRun.getSliceCommand(resultFilename, fileList, positionList)
		else:
			self._saveCombinedSTL(resultFilename + "_temp_.stl")
			sliceCommand = sliceRun.getSliceCommand(resultFilename, [resultFilename + "_temp_.stl"], [profile.getMachineCenterCoords()])

		pspw = ProjectSliceProgressWindow(sliceCommand, resultFilename, len(self.list))
		pspw.Centre()
		pspw.Show(True)

	def getExtraHeadSize(self):
		extraSizeMin = self.headSizeMin
		extraSizeMax = self.headSizeMax
		if profile.getProfileSettingFloat('skirt_line_count') > 0:
			skirtSize = profile.getProfileSettingFloat('skirt_line_count') * profile.calculateEdgeWidth() + profile.getProfileSettingFloat('skirt_gap')
			extraSizeMin = extraSizeMin + numpy.array([skirtSize, skirtSize, 0])
			extraSizeMax = extraSizeMax + numpy.array([skirtSize, skirtSize, 0])
		if profile.getProfileSetting('enable_raft') != 'False':
			raftSize = profile.getProfileSettingFloat('raft_margin') * 2
			extraSizeMin = extraSizeMin + numpy.array([raftSize, raftSize, 0])
			extraSizeMax = extraSizeMax + numpy.array([raftSize, raftSize, 0])
		if profile.getProfileSetting('support') != 'None':
			extraSizeMin = extraSizeMin + numpy.array([3.0, 0, 0])
			extraSizeMax = extraSizeMax + numpy.array([3.0, 0, 0])

		if self.printMode == 1:
			extraSizeMin = numpy.array([6.0, 6.0, 0])
			extraSizeMax = numpy.array([6.0, 6.0, 0])
		
		return extraSizeMin, extraSizeMax

class PreviewGLCanvas(openglGui.glGuiPanel):
	def __init__(self, parent, projectPlannerWindow):
		super(PreviewGLCanvas, self).__init__(parent)
		self.parent = projectPlannerWindow
		wx.EVT_MOUSEWHEEL(self, self.OnMouseWheel)
		self.yaw = 30
		self.pitch = 60
		self.offsetX = 0
		self.offsetY = 0
		self.view3D = self.parent.alwaysAutoPlace
		if self.view3D:
			self.zoom = 300
		else:
			self.zoom = self.parent.machineSize[0] / 2 + 10
		self.dragType = ''
		self.viewport = None
		self.allowDrag = False
		self.tempMatrix = None

		self.objColor = profile.getPreferenceColour('model_colour')

	def OnMouseLeftDown(self,e):
		self.allowDrag = True
		if not self.parent.alwaysAutoPlace and not self.view3D:
			p0 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 0, self.modelMatrix, self.projMatrix, self.viewport)
			p1 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 1, self.modelMatrix, self.projMatrix, self.viewport)
			p0 -= self.viewTarget
			p1 -= self.viewTarget
			p0 -= self.getObjectCenterPos() - self.viewTarget
			p1 -= self.getObjectCenterPos() - self.viewTarget
			cursorZ0 = p0 - (p1 - p0) * (p0[2] / (p1[2] - p0[2]))

			for item in self.parent.list:
				iMin =-item.getSize() / 2 + numpy.array([item.centerX, item.centerY, 0])
				iMax = item.getSize() / 2 + numpy.array([item.centerX, item.centerY, 0])
				if iMin[0] <= cursorZ0[0] <= iMax[0] and iMin[1] <= cursorZ0[1] <= iMax[1]:
					self.parent.selection = item
					self.parent._updateListbox()
					self.parent.OnListSelect(None)

	def OnMouseMotion(self,e):
		if self.viewport is not None:
			p0 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 0, self.modelMatrix, self.projMatrix, self.viewport)
			p1 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 1, self.modelMatrix, self.projMatrix, self.viewport)
			p0 -= self.viewTarget
			p1 -= self.viewTarget
			p0 -= self.getObjectCenterPos() - self.viewTarget
			p1 -= self.getObjectCenterPos() - self.viewTarget
			if not e.Dragging() or self.dragType != 'tool':
				self.parent.tool.OnMouseMove(p0, p1)
		else:
			p0 = [0,0,0]
			p1 = [1,0,0]

		if self.allowDrag and e.Dragging() and e.LeftIsDown():
			if self.dragType == '':
				#Define the drag type depending on the cursor position.
				self.dragType = 'viewRotate'
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
				elif not self.parent.alwaysAutoPlace:
					item = self.parent.selection
					if item is not None:
						item.centerX += float(e.GetX() - self.oldX) * self.zoom / self.GetSize().GetHeight() * 2
						item.centerY -= float(e.GetY() - self.oldY) * self.zoom / self.GetSize().GetHeight() * 2
						item.clampXY()
			elif self.dragType == 'tool':
				self.parent.tool.OnDrag(p0, p1)
		else:
			if self.dragType != '':
				if self.tempMatrix is not None:
					self.parent.selection.matrix *= self.tempMatrix
					self.parent.selection.updateMatrix()
					self.tempMatrix = None
				self.parent.tool.OnDragEnd()
				self.dragType = ''
			self.allowDrag = False
		if e.Dragging() and e.RightIsDown():
			if self.view3D:
				self.zoom += e.GetY() - self.oldY
				if self.zoom < 1:
					self.zoom = 1
			self.Refresh()
		self.oldX = e.GetX()
		self.oldY = e.GetY()
	
	def OnMouseWheel(self,e):
		if self.view3D:
			self.zoom *= 1.0 - float(e.GetWheelRotation() / e.GetWheelDelta()) / 10.0
			if self.zoom < 1.0:
				self.zoom = 1.0
			self.Refresh()
	
	def OnEraseBackground(self,event):
		#Workaround for windows background redraw flicker.
		pass
	
	def OnSize(self,event):
		self.Refresh()

	def OnPaint(self,event):
		opengl.InitGL(self, self.view3D, self.zoom)
		if self.view3D:
			glTranslate(0,0,-self.zoom)
			glRotate(-self.pitch, 1,0,0)
			glRotate(self.yaw, 0,0,1)
		self.viewTarget = self.parent.machineSize / 2
		self.viewTarget[2] = 0
		glTranslate(-self.viewTarget[0], -self.viewTarget[1], -self.viewTarget[2])

		self.viewport = glGetIntegerv(GL_VIEWPORT)
		self.modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
		self.projMatrix = glGetDoublev(GL_PROJECTION_MATRIX)

		self.OnDraw()

	def OnDraw(self):
		machineSize = self.parent.machineSize
		extraSizeMin, extraSizeMax = self.parent.getExtraHeadSize()

		for item in self.parent.list:
			item.validPlacement = True
			item.gotHit = False
		
		for idx1 in xrange(0, len(self.parent.list)):
			item = self.parent.list[idx1]
			iMin1 =-item.getSize() / 2 + numpy.array([item.centerX, item.centerY, 0]) - extraSizeMin #- self.parent.extruderOffset[item.extruder]
			iMax1 = item.getSize() / 2 + numpy.array([item.centerX, item.centerY, 0]) + extraSizeMax #- self.parent.extruderOffset[item.extruder]
			if iMin1[0] < -self.parent.headSizeMin[0] or iMin1[1] < -self.parent.headSizeMin[1]:
				item.validPlacement = False
			if iMax1[0] > machineSize[0] + self.parent.headSizeMax[0] or iMax1[1] > machineSize[1] + self.parent.headSizeMax[1]:
				item.validPlacement = False
			for idx2 in xrange(0, idx1):
				item2 = self.parent.list[idx2]
				iMin2 =-item2.getSize() / 2 + numpy.array([item2.centerX, item2.centerY, 0])
				iMax2 = item2.getSize() / 2 + numpy.array([item2.centerX, item2.centerY, 0])
				if item != item2 and iMax1[0] >= iMin2[0] and iMin1[0] <= iMax2[0] and iMax1[1] >= iMin2[1] and iMin1[1] <= iMax2[1]:
					item.validPlacement = False
					item2.gotHit = True
		
		seenSelected = False
		for item in self.parent.list:
			if item == self.parent.selection:
				seenSelected = True
			if item.modelDisplayList is None:
				item.modelDisplayList = glGenLists(1);
			if item.modelDirty:
				item.modelDirty = False
				glNewList(item.modelDisplayList, GL_COMPILE)
				opengl.DrawMesh(item.mesh)
				glEndList()
			
			if item.validPlacement:
				if self.parent.selection == item:
					glLightfv(GL_LIGHT0, GL_DIFFUSE,  map(lambda x: x + 0.2, self.objColor))
					glLightfv(GL_LIGHT0, GL_AMBIENT,  map(lambda x: x / 2, self.objColor))
				else:
					glLightfv(GL_LIGHT0, GL_DIFFUSE,  self.objColor)
					glLightfv(GL_LIGHT0, GL_AMBIENT,  map(lambda x: x / 2, self.objColor))
			else:
				if self.parent.selection == item:
					glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 0.0, 0.0, 0.0])
					glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.2, 0.0, 0.0, 0.0])
				else:
					glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 0.0, 0.0, 0.0])
					glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.2, 0.0, 0.0, 0.0])
			glPushMatrix()
			
			glEnable(GL_LIGHTING)
			glTranslate(item.centerX, item.centerY, 0)
			vMin = item.getMinimum()
			vMax = item.getMaximum()
			offset = - vMin - (vMax - vMin) / 2
			matrix = opengl.convert3x3MatrixTo4x4(item.matrix)
			glPushMatrix()
			glTranslate(0, 0, item.getSize()[2]/2)
			if self.tempMatrix is not None and item == self.parent.selection:
				tempMatrix = opengl.convert3x3MatrixTo4x4(self.tempMatrix)
				glMultMatrixf(tempMatrix)
			glTranslate(0, 0, -item.getSize()[2]/2)
			glTranslate(offset[0], offset[1], -vMin[2])
			glMultMatrixf(matrix)
			glCallList(item.modelDisplayList)
			glPopMatrix()

			vMin =-item.getSize() / 2
			vMax = item.getSize() / 2
			vMax[2] -= vMin[2]
			vMin[2] = 0
			vMinHead = vMin - extraSizeMin# - self.parent.extruderOffset[item.extruder]
			vMaxHead = vMax + extraSizeMax# - self.parent.extruderOffset[item.extruder]

			glDisable(GL_LIGHTING)

			if not self.parent.alwaysAutoPlace:
				glLineWidth(1)
				if self.parent.selection == item:
					if item.gotHit:
						glColor3f(1.0,0.0,0.3)
					else:
						glColor3f(1.0,0.0,1.0)
					opengl.DrawBox(vMin, vMax)
					if item.gotHit:
						glColor3f(1.0,0.3,0.0)
					else:
						glColor3f(1.0,1.0,0.0)
					opengl.DrawBox(vMinHead, vMaxHead)
				elif seenSelected:
					if item.gotHit:
						glColor3f(0.5,0.0,0.1)
					else:
						glColor3f(0.5,0.0,0.5)
					opengl.DrawBox(vMinHead, vMaxHead)
				else:
					if item.gotHit:
						glColor3f(0.7,0.1,0.0)
					else:
						glColor3f(0.7,0.7,0.0)
					opengl.DrawBox(vMin, vMax)
			
			glPopMatrix()
		
		opengl.DrawMachine(util3d.Vector3(machineSize[0], machineSize[1], machineSize[2]))

		if self.parent.selection is not None:
			glPushMatrix()
			glTranslate(self.parent.selection.centerX, self.parent.selection.centerY, self.parent.selection.getSize()[2]/2)
			self.parent.tool.OnDraw()
			glPopMatrix()

	def getObjectSize(self):
		if self.parent.selection is not None:
			return self.parent.selection.getSize()
		return [0.0,0.0,0.0]
	def getObjectBoundaryCircle(self):
		if self.parent.selection is not None:
			return self.parent.selection.getBoundaryCircle()
		return 0.0
	def getObjectMatrix(self):
		return self.parent.selection.matrix
	def getObjectCenterPos(self):
		if self.parent.selection is None:
			return [0,0,0]
		return [self.parent.selection.centerX, self.parent.selection.centerY, self.getObjectSize()[2] / 2]

class ProjectSliceProgressWindow(wx.Frame):
	def __init__(self, sliceCommand, resultFilename, fileCount):
		super(ProjectSliceProgressWindow, self).__init__(None, title='Cura')
		self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
		
		self.sliceCommand = sliceCommand
		self.resultFilename = resultFilename
		self.fileCount = fileCount
		self.abort = False
		self.prevStep = 'start'
		self.totalDoneFactor = 0.0
		self.startTime = time.time()
		self.sliceStartTime = time.time()
		
		self.sizer = wx.GridBagSizer(2, 2) 
		self.statusText = wx.StaticText(self, -1, "Building: %s" % (resultFilename))
		self.progressGauge = wx.Gauge(self, -1)
		self.progressGauge.SetRange(10000)
		self.progressGauge2 = wx.Gauge(self, -1)
		self.progressGauge2.SetRange(self.fileCount)
		self.progressGauge2.SetValue(-1)
		self.abortButton = wx.Button(self, -1, "Abort")
		self.sizer.Add(self.statusText, (0,0), span=(1,5))
		self.sizer.Add(self.progressGauge, (1, 0), span=(1,5), flag=wx.EXPAND)
		self.sizer.Add(self.progressGauge2, (2, 0), span=(1,5), flag=wx.EXPAND)

		self.sizer.Add(self.abortButton, (3,0), span=(1,5), flag=wx.ALIGN_CENTER)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableRow(0)

		self.Bind(wx.EVT_BUTTON, self.OnAbort, self.abortButton)
		self.SetSizer(self.sizer)
		self.Layout()
		self.Fit()
		
		threading.Thread(target=self.OnRun).start()

	def OnAbort(self, e):
		if self.abort:
			self.Close()
		else:
			self.abort = True
			self.abortButton.SetLabel('Close')

	def SetProgress(self, stepName, layer, maxLayer):
		if self.prevStep != stepName:
			if stepName == 'slice':
				self.progressGauge2.SetValue(self.progressGauge2.GetValue() + 1)
				self.totalDoneFactor = 0
			self.totalDoneFactor += sliceRun.sliceStepTimeFactor[self.prevStep]
			newTime = time.time()
			#print "#####" + str(newTime-self.startTime) + " " + self.prevStep + " -> " + stepName
			self.startTime = newTime
			self.prevStep = stepName
		
		progresValue = ((self.totalDoneFactor + sliceRun.sliceStepTimeFactor[stepName] * layer / maxLayer) / sliceRun.totalRunTimeFactor) * 10000
		self.progressGauge.SetValue(int(progresValue))
		self.statusText.SetLabel(stepName + " [" + str(layer) + "/" + str(maxLayer) + "]")
		taskbar.setProgress(self, 10000 * self.progressGauge2.GetValue() + int(progresValue), 10000 * self.fileCount)
	
	def OnRun(self):
		self.progressLog = []
		p = sliceRun.startSliceCommandProcess(self.sliceCommand)
		line = p.stdout.readline()
		while(len(line) > 0):
			line = line.rstrip()
			if line[0:9] == "Progress[" and line[-1:] == "]":
				progress = line[9:-1].split(":")
				if len(progress) > 2:
					maxValue = int(progress[2])
				wx.CallAfter(self.SetProgress, progress[0], int(progress[1]), maxValue)
			else:
				self.progressLog.append(line)
				wx.CallAfter(self.statusText.SetLabel, line)
			if self.abort:
				p.terminate()
				wx.CallAfter(self.statusText.SetLabel, "Aborted by user.")
				return
			line = p.stdout.readline()
		line = p.stderr.readline()
		while len(line) > 0:
			line = line.rstrip()
			self.progressLog.append(line)
			line = p.stderr.readline()
		self.returnCode = p.wait()
		self.progressGauge2.SetValue(self.fileCount)

		gcode = gcodeInterpreter.gcode()
		gcode.load(self.resultFilename)
		
		self.abort = True
		sliceTime = time.time() - self.sliceStartTime
		status = "Build: %s" % (self.resultFilename)
		status += "\nSlicing took: %02d:%02d" % (sliceTime / 60, sliceTime % 60)
		status += "\nFilament: %.2fm %.2fg" % (gcode.extrusionAmount / 1000, gcode.calculateWeight() * 1000)
		status += "\nPrint time: %02d:%02d" % (int(gcode.totalMoveTimeMinute / 60), int(gcode.totalMoveTimeMinute % 60))
		cost = gcode.calculateCost()
		if cost is not None:
			status += "\nCost: %s" % (cost)
		profile.replaceGCodeTags(self.resultFilename, gcode)
		wx.CallAfter(self.statusText.SetLabel, status)
		wx.CallAfter(self.OnSliceDone)
	
	def _adjustNumberInLine(self, line, tag, f):
		m = re.search('^(.*'+tag+')([0-9\.]*)(.*)$', line)
		return m.group(1) + str(float(m.group(2)) + f) + m.group(3) + '\n'
	
	def OnSliceDone(self):
		self.abortButton.Destroy()
		self.closeButton = wx.Button(self, -1, "Close")
		self.printButton = wx.Button(self, -1, "Print")
		self.logButton = wx.Button(self, -1, "Show log")
		self.sizer.Add(self.closeButton, (3,0), span=(1,1))
		self.sizer.Add(self.printButton, (3,1), span=(1,1))
		self.sizer.Add(self.logButton, (3,2), span=(1,1))
		if explorer.hasExplorer():
			self.openFileLocationButton = wx.Button(self, -1, "Open file location")
			self.Bind(wx.EVT_BUTTON, self.OnOpenFileLocation, self.openFileLocationButton)
			self.sizer.Add(self.openFileLocationButton, (3,3), span=(1,1))
		if profile.getPreference('sdpath') != '':
			self.copyToSDButton = wx.Button(self, -1, "To SDCard")
			self.Bind(wx.EVT_BUTTON, self.OnCopyToSD, self.copyToSDButton)
			self.sizer.Add(self.copyToSDButton, (3,4), span=(1,1))
		self.Bind(wx.EVT_BUTTON, self.OnAbort, self.closeButton)
		self.Bind(wx.EVT_BUTTON, self.OnPrint, self.printButton)
		self.Bind(wx.EVT_BUTTON, self.OnShowLog, self.logButton)
		self.Layout()
		self.Fit()
		taskbar.setBusy(self, False)

	def OnCopyToSD(self, e):
		filename = os.path.basename(self.resultFilename)
		if profile.getPreference('sdshortnames') == 'True':
			filename = sliceRun.getShortFilename(filename)
		shutil.copy(self.resultFilename, os.path.join(profile.getPreference('sdpath'), filename))
	
	def OnOpenFileLocation(self, e):
		explorer.openExplorer(self.resultFilename)
	
	def OnPrint(self, e):
		printWindow.printFile(self.resultFilename)

	def OnShowLog(self, e):
		LogWindow('\n'.join(self.progressLog))

class preferencesDialog(wx.Frame):
	def __init__(self, parent):
		super(preferencesDialog, self).__init__(None, title="Project Planner Preferences", style=wx.DEFAULT_DIALOG_STYLE)
		
		self.parent = parent
		wx.EVT_CLOSE(self, self.OnClose)

		self.panel = configBase.configPanelBase(self)
		extruderAmount = int(profile.getPreference('extruder_amount'))
		
		left, right, main = self.panel.CreateConfigPanel(self)
		configBase.TitleRow(left, 'User interface settings')
		c = configBase.SettingRow(left, 'Always auto place objects in planner', 'planner_always_autoplace', True, 'Disable this to allow manual placement in the project planner (requires restart).', type = 'preference')
		configBase.TitleRow(left, 'Machine head size')
		c = configBase.SettingRow(left, 'Head size - X towards home (mm)', 'extruder_head_size_min_x', '0', 'Size of your printer head in the X direction, on the Ultimaker your fan is in this direction.', type = 'preference')
		validators.validFloat(c, 0.1)
		c = configBase.SettingRow(left, 'Head size - X towards end (mm)', 'extruder_head_size_max_x', '0', 'Size of your printer head in the X direction.', type = 'preference')
		validators.validFloat(c, 0.1)
		c = configBase.SettingRow(left, 'Head size - Y towards home (mm)', 'extruder_head_size_min_y', '0', 'Size of your printer head in the Y direction.', type = 'preference')
		validators.validFloat(c, 0.1)
		c = configBase.SettingRow(left, 'Head size - Y towards end (mm)', 'extruder_head_size_max_y', '0', 'Size of your printer head in the Y direction.', type = 'preference')
		validators.validFloat(c, 0.1)
		c = configBase.SettingRow(left, 'Head gantry height (mm)', 'extruder_head_size_height', '0', 'The tallest object height that will always fit under your printers gantry system when the printer head is at the lowest Z position.', type = 'preference')
		validators.validFloat(c)
		
		self.okButton = wx.Button(left, -1, 'Ok')
		left.GetSizer().Add(self.okButton, (left.GetSizer().GetRows(), 1))
		self.okButton.Bind(wx.EVT_BUTTON, self.OnClose)
		
		self.MakeModal(True)
		main.Fit()
		self.Fit()

	def OnClose(self, e):
		self.parent.headSizeMin = numpy.array([profile.getPreferenceFloat('extruder_head_size_min_x'), profile.getPreferenceFloat('extruder_head_size_min_y'),0])
		self.parent.headSizeMax = numpy.array([profile.getPreferenceFloat('extruder_head_size_max_x'), profile.getPreferenceFloat('extruder_head_size_max_y'),0])
		self.parent.Refresh()

		self.MakeModal(False)
		self.Destroy()

class LogWindow(wx.Frame):
	def __init__(self, logText):
		super(LogWindow, self).__init__(None, title="Slice log")
		self.textBox = wx.TextCtrl(self, -1, logText, style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_READONLY)
		self.SetSize((400,300))
		self.Centre()
		self.Show(True)
