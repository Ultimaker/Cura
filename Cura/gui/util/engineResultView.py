__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import numpy
import math
import threading

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.util import profile
from Cura.gui.util import openglHelpers
from Cura.gui.util import openglGui

class engineResultView(object):
	def __init__(self, parent):
		self._parent = parent
		self._result = None
		self._enabled = False
		self._gcodeLoadProgress = 0
		self._resultLock = threading.Lock()
		self._layerVBOs = []
		self._layer20VBOs = []

		self.layerSelect = openglGui.glSlider(self._parent, 10000, 0, 1, (-1,-2), lambda : self._parent.QueueRefresh())

	def setResult(self, result):
		if self._result == result:
			return
		if result is None:
			self.setEnabled(False)

		self._resultLock.acquire()
		self._result = result

		#Clean the saved VBO's
		for layer in self._layerVBOs:
			for typeName in layer.keys():
				self._parent.glReleaseList.append(layer[typeName])
		for layer in self._layer20VBOs:
			for typeName in layer.keys():
				self._parent.glReleaseList.append(layer[typeName])
		self._layerVBOs = []
		self._layer20VBOs = []
		self._resultLock.release()

	def setEnabled(self, enabled):
		self._enabled = enabled
		self.layerSelect.setHidden(not enabled)

	def _gcodeLoadCallback(self, result, progress):
		if result != self._result:
			#Abort loading from this thread.
			return True
		self._gcodeLoadProgress = progress
		self._parent._queueRefresh()
		return False

	def OnDraw(self):
		if not self._enabled:
			return

		self._resultLock.acquire()
		result = self._result
		if result is not None:
			gcodeLayers = result.getGCodeLayers(self._gcodeLoadCallback)
			if result._polygons is not None and len(result._polygons) > 0:
				self.layerSelect.setRange(1, len(result._polygons))
			elif gcodeLayers is not None and len(gcodeLayers) > 0:
				self.layerSelect.setRange(1, len(gcodeLayers))
		else:
			gcodeLayers = None

		glPushMatrix()
		glEnable(GL_BLEND)
		if profile.getMachineSetting('machine_center_is_zero') != 'True':
			glTranslate(-profile.getMachineSettingFloat('machine_width') / 2, -profile.getMachineSettingFloat('machine_depth') / 2, 0)
		glLineWidth(2)

		layerNr = self.layerSelect.getValue()
		if layerNr == self.layerSelect.getMaxValue() and result is not None and len(result._polygons) > 0:
			layerNr = max(layerNr, len(result._polygons))
		if len(result._polygons) > layerNr-1 and 'inset0' in result._polygons[layerNr-1] and len(result._polygons[layerNr-1]['inset0']) > 0 and len(result._polygons[layerNr-1]['inset0'][0]) > 0:
			viewZ = result._polygons[layerNr-1]['inset0'][0][0][2]
		else:
			viewZ = (layerNr - 1) * profile.getProfileSettingFloat('layer_height') + profile.getProfileSettingFloat('bottom_thickness')
		self._parent._viewTarget[2] = viewZ
		msize = max(profile.getMachineSettingFloat('machine_width'), profile.getMachineSettingFloat('machine_depth'))
		lineTypeList = [
			('inset0',     'WALL-OUTER', [1,0,0,1]),
			('insetx',     'WALL-INNER', [0,1,0,1]),
			('openoutline', None,        [1,0,0,1]),
			('skin',       'FILL',       [1,1,0,1]),
			('infill',      None,        [1,1,0,1]),
			('support',    'SUPPORT',    [0,1,1,1]),
			('skirt',      'SKIRT',      [0,1,1,1]),
			('outline',     None,        [0,0,0,1])
		]
		n = layerNr - 1
		generatedVBO = False
		if result is not None:
			while n >= 0:
				if layerNr - n > 30 and n % 20 == 0 and len(result._polygons) > 0:
					idx = n / 20
					while len(self._layer20VBOs) < idx + 1:
						self._layer20VBOs.append({})
					if result._polygons is not None and n + 20 < len(result._polygons):
						layerVBOs = self._layer20VBOs[idx]
						for typeName, typeNameGCode, color in lineTypeList:
							allow = typeName in result._polygons[n + 19]
							if typeName == 'skirt':
								for i in xrange(0, 20):
									if typeName in result._polygons[n + i]:
										allow = True
							if allow:
								if typeName not in layerVBOs:
									if generatedVBO:
										continue
									polygons = []
									for i in xrange(0, 20):
										if typeName in result._polygons[n + i]:
											polygons += result._polygons[n + i][typeName]
									layerVBOs[typeName] = self._polygonsToVBO_lines(polygons)
									generatedVBO = True
								glColor4f(color[0]*0.5,color[1]*0.5,color[2]*0.5,color[3])
								layerVBOs[typeName].render()
					n -= 20
				else:
					c = 1.0 - ((layerNr - n) - 1) * 0.05
					c = max(0.5, c)
					while len(self._layerVBOs) < n + 1:
						self._layerVBOs.append({})
					layerVBOs = self._layerVBOs[n]
					if gcodeLayers is not None and ((layerNr - 10 < n < (len(gcodeLayers) - 1)) or len(result._polygons) < 1):
						for typeNamePolygons, typeName, color in lineTypeList:
							if typeName is None:
								continue
							if 'GCODE-' + typeName not in layerVBOs:
								layerVBOs['GCODE-' + typeName] = self._gcodeToVBO_quads(gcodeLayers[n+1:n+2], typeName)
							glColor4f(color[0]*c,color[1]*c,color[2]*c,color[3])
							layerVBOs['GCODE-' + typeName].render()

						if n == layerNr - 1:
							if 'GCODE-MOVE' not in layerVBOs:
								layerVBOs['GCODE-MOVE'] = self._gcodeToVBO_lines(gcodeLayers[n+1:n+2])
							glColor4f(0,0,c,1)
							layerVBOs['GCODE-MOVE'].render()
					elif n < len(result._polygons):
						polygons = result._polygons[n]
						for typeName, typeNameGCode, color in lineTypeList:
							if typeName in polygons:
								if typeName not in layerVBOs:
									layerVBOs[typeName] = self._polygonsToVBO_lines(polygons[typeName])
								glColor4f(color[0]*c,color[1]*c,color[2]*c,color[3])
								layerVBOs[typeName].render()
					n -= 1
		glPopMatrix()
		if generatedVBO:
			self._parent._queueRefresh()

		if gcodeLayers is not None and self._gcodeLoadProgress != 0.0 and self._gcodeLoadProgress != 1.0:
			glPushMatrix()
			glLoadIdentity()
			glTranslate(0,-0.8,-2)
			glColor4ub(60,60,60,255)
			openglHelpers.glDrawStringCenter(_("Loading toolpath for visualization (%d%%)") % (self._gcodeLoadProgress * 100))
			glPopMatrix()
		self._resultLock.release()

	def _polygonsToVBO_lines(self, polygons):
		verts = numpy.zeros((0, 3), numpy.float32)
		indices = numpy.zeros((0), numpy.uint32)
		for poly in polygons:
			if len(poly) > 2:
				i = numpy.arange(len(verts), len(verts) + len(poly) + 1, 1, numpy.uint32)
				i[-1] = len(verts)
				i = numpy.dstack((i[0:-1],i[1:])).flatten()
			else:
				i = numpy.arange(len(verts), len(verts) + len(poly), 1, numpy.uint32)
			indices = numpy.concatenate((indices, i), 0)
			verts = numpy.concatenate((verts, poly), 0)
		return openglHelpers.GLVBO(GL_LINES, verts, indicesArray=indices)

	def _polygonsToVBO_quads(self, polygons):
		verts = numpy.zeros((0, 3), numpy.float32)
		indices = numpy.zeros((0), numpy.uint32)
		for poly in polygons:
			i = numpy.arange(len(verts), len(verts) + len(poly) + 1, 1, numpy.uint32)
			i2 = numpy.arange(len(verts) + len(poly), len(verts) + len(poly) + len(poly) + 1, 1, numpy.uint32)
			i[-1] = len(verts)
			i2[-1] = len(verts) + len(poly)
			i = numpy.dstack((i[0:-1],i2[0:-1],i2[1:],i[1:])).flatten()
			indices = numpy.concatenate((indices, i), 0)
			verts = numpy.concatenate((verts, poly), 0)
			verts = numpy.concatenate((verts, poly * numpy.array([1,0,1],numpy.float32) + numpy.array([0,-100,0],numpy.float32)), 0)
		return openglHelpers.GLVBO(GL_QUADS, verts, indicesArray=indices)

	def _gcodeToVBO_lines(self, gcodeLayers, extrudeType):
		if ':' in extrudeType:
			extruder = int(extrudeType[extrudeType.find(':')+1:])
			extrudeType = extrudeType[0:extrudeType.find(':')]
		else:
			extruder = None
		verts = numpy.zeros((0, 3), numpy.float32)
		indices = numpy.zeros((0), numpy.uint32)
		for layer in gcodeLayers:
			for path in layer:
				if path['type'] == 'extrude' and path['pathType'] == extrudeType and (extruder is None or path['extruder'] == extruder):
					i = numpy.arange(len(verts), len(verts) + len(path['points']), 1, numpy.uint32)
					i = numpy.dstack((i[0:-1],i[1:])).flatten()
					indices = numpy.concatenate((indices, i), 0)
					verts = numpy.concatenate((verts, path['points']))
		return openglHelpers.GLVBO(GL_LINES, verts, indicesArray=indices)

	def _gcodeToVBO_quads(self, gcodeLayers, extrudeType):
		useFilamentArea = profile.getMachineSetting('gcode_flavor') == 'UltiGCode'
		filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
		filamentArea = math.pi * filamentRadius * filamentRadius

		if ':' in extrudeType:
			extruder = int(extrudeType[extrudeType.find(':')+1:])
			extrudeType = extrudeType[0:extrudeType.find(':')]
		else:
			extruder = None

		verts = numpy.zeros((0, 3), numpy.float32)
		indices = numpy.zeros((0), numpy.uint32)
		for layer in gcodeLayers:
			for path in layer:
				if path['type'] == 'extrude' and path['pathType'] == extrudeType and (extruder is None or path['extruder'] == extruder):
					a = path['points']
					if extrudeType == 'FILL':
						a[:,2] += 0.01

					#Construct the normals of each line 90deg rotated on the X/Y plane
					normals = a[1:] - a[:-1]
					lengths = numpy.sqrt(normals[:,0]**2 + normals[:,1]**2)
					normals[:,0], normals[:,1] = -normals[:,1] / lengths, normals[:,0] / lengths
					normals[:,2] /= lengths

					ePerDist = path['extrusion'][1:] / lengths
					if useFilamentArea:
						lineWidth = ePerDist / path['layerThickness'] / 2.0
					else:
						lineWidth = ePerDist * (filamentArea / path['layerThickness'] / 2)

					normals[:,0] *= lineWidth
					normals[:,1] *= lineWidth

					b = numpy.zeros((len(a)-1, 0), numpy.float32)
					b = numpy.concatenate((b, a[1:] + normals), 1)
					b = numpy.concatenate((b, a[1:] - normals), 1)
					b = numpy.concatenate((b, a[:-1] - normals), 1)
					b = numpy.concatenate((b, a[:-1] + normals), 1)
					b = b.reshape((len(b) * 4, 3))

					i = numpy.arange(len(verts), len(verts) + len(b), 1, numpy.uint32)

					verts = numpy.concatenate((verts, b))
					indices = numpy.concatenate((indices, i))
		return openglHelpers.GLVBO(GL_QUADS, verts, indicesArray=indices)

	def _gcodeToVBO_lines(self, gcodeLayers):
		verts = numpy.zeros((0,3), numpy.float32)
		indices = numpy.zeros((0), numpy.uint32)
		for layer in gcodeLayers:
			for path in layer:
				if path['type'] == 'move':
					a = path['points'] + numpy.array([0,0,0.02], numpy.float32)
					i = numpy.arange(len(verts), len(verts) + len(a), 1, numpy.uint32)
					i = numpy.dstack((i[0:-1],i[1:])).flatten()
					verts = numpy.concatenate((verts, a))
					indices = numpy.concatenate((indices, i))
				if path['type'] == 'retract':
					a = path['points'] + numpy.array([0,0,0.02], numpy.float32)
					a = numpy.concatenate((a[:-1], a[1:] + numpy.array([0,0,1], numpy.float32)), 1)
					a = a.reshape((len(a) * 2, 3))
					i = numpy.arange(len(verts), len(verts) + len(a), 1, numpy.uint32)
					verts = numpy.concatenate((verts, a))
					indices = numpy.concatenate((indices, i))
		return openglHelpers.GLVBO(GL_LINES, verts, indicesArray=indices)

	def OnKeyChar(self, keyCode):
		if not self._enabled:
			return
		#TODO: This is strange behaviour. Overloaded functionality of keyboard buttons!
		if wx.GetKeyState(wx.WXK_SHIFT) or wx.GetKeyState(wx.WXK_CONTROL):
			if keyCode == wx.WXK_UP:
				self.layerSelect.setValue(self.layerSelect.getValue() + 1)
				self._parent.QueueRefresh()
				return True
			elif keyCode == wx.WXK_DOWN:
				self.layerSelect.setValue(self.layerSelect.getValue() - 1)
				self._parent.QueueRefresh()
				return True
			elif keyCode == wx.WXK_PAGEUP:
				self.layerSelect.setValue(self.layerSelect.getValue() + 10)
				self._parent.QueueRefresh()
				return True
			elif keyCode == wx.WXK_PAGEDOWN:
				self.layerSelect.setValue(self.layerSelect.getValue() - 10)
				self._parent.QueueRefresh()
				return True
		return False
