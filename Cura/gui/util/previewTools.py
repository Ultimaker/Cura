from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import wx
import numpy

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.gui.util import opengl

class toolNone(object):
	def __init__(self, parent):
		self.parent = parent

	def OnMouseMove(self, p0, p1):
		pass

	def OnDragStart(self, p0, p1):
		return False

	def OnDrag(self, p0, p1):
		pass

	def OnDragEnd(self):
		pass

	def OnDraw(self):
		pass

class toolInfo(object):
	def __init__(self, parent):
		self.parent = parent

	def OnMouseMove(self, p0, p1):
		pass

	def OnDragStart(self, p0, p1):
		return False

	def OnDrag(self, p0, p1):
		pass

	def OnDragEnd(self):
		pass

	def OnDraw(self):
		glDisable(GL_LIGHTING)
		glDisable(GL_BLEND)
		glDisable(GL_DEPTH_TEST)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor3ub(0,0,0)
		size = self.parent.getObjectSize()
		radius = self.parent.getObjectBoundaryCircle()
		glPushMatrix()
		glTranslate(0,0,size[2]/2 + 5)
		glRotate(-self.parent.yaw, 0,0,1)
		if self.parent.pitch < 80:
			glTranslate(0, radius + 5,0)
		elif self.parent.pitch < 100:
			glTranslate(0, (radius + 5) * (90 - self.parent.pitch) / 10,0)
		else:
			glTranslate(0,-(radius + 5),0)
		opengl.glDrawStringCenter("%dx%dx%d" % (size[0], size[1], size[2]))
		glPopMatrix()

		glColor(255,255,255)
		size = size / 2
		glLineWidth(1)
		glBegin(GL_LINES)
		glVertex3f(size[0], size[1], size[2])
		glVertex3f(size[0], size[1], size[2]/4*3)
		glVertex3f(size[0], size[1], size[2])
		glVertex3f(size[0], size[1]/4*3, size[2])
		glVertex3f(size[0], size[1], size[2])
		glVertex3f(size[0]/4*3, size[1], size[2])

		glVertex3f(-size[0], -size[1], size[2])
		glVertex3f(-size[0], -size[1], size[2]/4*3)
		glVertex3f(-size[0], -size[1], size[2])
		glVertex3f(-size[0], -size[1]/4*3, size[2])
		glVertex3f(-size[0], -size[1], size[2])
		glVertex3f(-size[0]/4*3, -size[1], size[2])

		glVertex3f(size[0], -size[1], -size[2])
		glVertex3f(size[0], -size[1], -size[2]/4*3)
		glVertex3f(size[0], -size[1], -size[2])
		glVertex3f(size[0], -size[1]/4*3, -size[2])
		glVertex3f(size[0], -size[1], -size[2])
		glVertex3f(size[0]/4*3, -size[1], -size[2])

		glVertex3f(-size[0], size[1], -size[2])
		glVertex3f(-size[0], size[1], -size[2]/4*3)
		glVertex3f(-size[0], size[1], -size[2])
		glVertex3f(-size[0], size[1]/4*3, -size[2])
		glVertex3f(-size[0], size[1], -size[2])
		glVertex3f(-size[0]/4*3, size[1], -size[2])
		glEnd()

class toolRotate(object):
	def __init__(self, parent):
		self.parent = parent
		self.rotateRingDist = 1.5
		self.rotateRingDistMin = 1.3
		self.rotateRingDistMax = 1.7
		self.dragPlane = None
		self.dragStartAngle = None
		self.dragEndAngle = None

	def _ProjectToPlanes(self, p0, p1):
		cursorX0 = p0 - (p1 - p0) * (p0[0] / (p1[0] - p0[0]))
		cursorY0 = p0 - (p1 - p0) * (p0[1] / (p1[1] - p0[1]))
		cursorZ0 = p0 - (p1 - p0) * (p0[2] / (p1[2] - p0[2]))
		cursorYZ = math.sqrt((cursorX0[1] * cursorX0[1]) + (cursorX0[2] * cursorX0[2]))
		cursorXZ = math.sqrt((cursorY0[0] * cursorY0[0]) + (cursorY0[2] * cursorY0[2]))
		cursorXY = math.sqrt((cursorZ0[0] * cursorZ0[0]) + (cursorZ0[1] * cursorZ0[1]))
		return cursorX0, cursorY0, cursorZ0, cursorYZ, cursorXZ, cursorXY

	def OnMouseMove(self, p0, p1):
		radius = self.parent.getObjectBoundaryCircle()
		cursorX0, cursorY0, cursorZ0, cursorYZ, cursorXZ, cursorXY = self._ProjectToPlanes(p0, p1)
		oldDragPlane = self.dragPlane
		if radius * self.rotateRingDistMin <= cursorXY <= radius * self.rotateRingDistMax or radius * self.rotateRingDistMin <= cursorYZ <= radius * self.rotateRingDistMax or radius * self.rotateRingDistMin <= cursorXZ <= radius * self.rotateRingDistMax:
			#self.parent.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
			if self.dragStartAngle is None:
				if radius * self.rotateRingDistMin <= cursorXY <= radius * self.rotateRingDistMax:
					self.dragPlane = 'XY'
				elif radius * self.rotateRingDistMin <= cursorXZ <= radius * self.rotateRingDistMax:
					self.dragPlane = 'XZ'
				else:
					self.dragPlane = 'YZ'
		else:
			if self.dragStartAngle is None:
				self.dragPlane = ''
			#self.parent.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

	def OnDragStart(self, p0, p1):
		radius = self.parent.getObjectBoundaryCircle()
		cursorX0, cursorY0, cursorZ0, cursorYZ, cursorXZ, cursorXY = self._ProjectToPlanes(p0, p1)
		if radius * self.rotateRingDistMin <= cursorXY <= radius * self.rotateRingDistMax or radius * self.rotateRingDistMin <= cursorYZ <= radius * self.rotateRingDistMax or radius * self.rotateRingDistMin <= cursorXZ <= radius * self.rotateRingDistMax:
			if radius * self.rotateRingDistMin <= cursorXY <= radius * self.rotateRingDistMax:
				self.dragPlane = 'XY'
				self.dragStartAngle = math.atan2(cursorZ0[1], cursorZ0[0]) * 180 / math.pi
			elif radius * self.rotateRingDistMin <= cursorXZ <= radius * self.rotateRingDistMax:
				self.dragPlane = 'XZ'
				self.dragStartAngle = math.atan2(cursorY0[2], cursorY0[0]) * 180 / math.pi
			else:
				self.dragPlane = 'YZ'
				self.dragStartAngle = math.atan2(cursorX0[2], cursorX0[1]) * 180 / math.pi
			self.dragEndAngle = self.dragStartAngle
			return True
		return False

	def OnDrag(self, p0, p1):
		cursorX0, cursorY0, cursorZ0, cursorYZ, cursorXZ, cursorXY = self._ProjectToPlanes(p0, p1)
		if self.dragPlane == 'XY':
			angle = math.atan2(cursorZ0[1], cursorZ0[0]) * 180 / math.pi
		elif self.dragPlane == 'XZ':
			angle = math.atan2(cursorY0[2], cursorY0[0]) * 180 / math.pi
		else:
			angle = math.atan2(cursorX0[2], cursorX0[1]) * 180 / math.pi
		diff = angle - self.dragStartAngle
		if wx.GetKeyState(wx.WXK_SHIFT):
			diff = round(diff / 1) * 1
		else:
			diff = round(diff / 15) * 15
		if diff > 180:
			diff -= 360
		if diff < -180:
			diff += 360
		rad = diff / 180.0 * math.pi
		self.dragEndAngle = self.dragStartAngle + diff
		if self.dragPlane == 'XY':
			self.parent.tempMatrix = numpy.matrix([[math.cos(rad), math.sin(rad), 0], [-math.sin(rad), math.cos(rad), 0], [0,0,1]], numpy.float64)
		elif self.dragPlane == 'XZ':
			self.parent.tempMatrix = numpy.matrix([[math.cos(rad), 0, math.sin(rad)], [0,1,0], [-math.sin(rad), 0, math.cos(rad)]], numpy.float64)
		else:
			self.parent.tempMatrix = numpy.matrix([[1,0,0], [0, math.cos(rad), math.sin(rad)], [0, -math.sin(rad), math.cos(rad)]], numpy.float64)

	def OnDragEnd(self):
		self.dragStartAngle = None

	def OnDraw(self):
		glDisable(GL_LIGHTING)
		glDisable(GL_BLEND)
		glDisable(GL_DEPTH_TEST)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		radius = self.parent.getObjectBoundaryCircle()
		glScalef(self.rotateRingDist * radius, self.rotateRingDist * radius, self.rotateRingDist * radius)
		if self.dragPlane == 'XY':
			glLineWidth(3)
			glColor4ub(255,64,64,255)
			if self.dragStartAngle is not None:
				glPushMatrix()
				glRotate(self.dragStartAngle, 0,0,1)
				glBegin(GL_LINES)
				glVertex3f(0,0,0)
				glVertex3f(1,0,0)
				glEnd()
				glPopMatrix()
				glPushMatrix()
				glRotate(self.dragEndAngle, 0,0,1)
				glBegin(GL_LINES)
				glVertex3f(0,0,0)
				glVertex3f(1,0,0)
				glEnd()
				glTranslatef(1.1,0,0)
				glColor4ub(0,0,0,255)
				opengl.glDrawStringCenter("%d" % (abs(self.dragEndAngle - self.dragStartAngle)))
				glColor4ub(255,64,64,255)
				glPopMatrix()
		else:
			glLineWidth(1)
			glColor4ub(128,0,0,255)
		glBegin(GL_LINE_LOOP)
		for i in xrange(0, 64):
			glVertex3f(math.cos(i/32.0*math.pi), math.sin(i/32.0*math.pi),0)
		glEnd()
		if self.dragPlane == 'YZ':
			glColor4ub(64,255,64,255)
			glLineWidth(3)
			if self.dragStartAngle is not None:
				glPushMatrix()
				glRotate(self.dragStartAngle, 1,0,0)
				glBegin(GL_LINES)
				glVertex3f(0,0,0)
				glVertex3f(0,1,0)
				glEnd()
				glPopMatrix()
				glPushMatrix()
				glRotate(self.dragEndAngle, 1,0,0)
				glBegin(GL_LINES)
				glVertex3f(0,0,0)
				glVertex3f(0,1,0)
				glEnd()
				glTranslatef(0,1.1,0)
				glColor4ub(0,0,0,255)
				opengl.glDrawStringCenter("%d" % (abs(self.dragEndAngle - self.dragStartAngle)))
				glColor4ub(64,255,64,255)
				glPopMatrix()
		else:
			glColor4ub(0,128,0,255)
			glLineWidth(1)
		glBegin(GL_LINE_LOOP)
		for i in xrange(0, 64):
			glVertex3f(0, math.cos(i/32.0*math.pi), math.sin(i/32.0*math.pi))
		glEnd()
		if self.dragPlane == 'XZ':
			glLineWidth(3)
			glColor4ub(255,255,0,255)
			if self.dragStartAngle is not None:
				glPushMatrix()
				glRotate(self.dragStartAngle, 0,-1,0)
				glBegin(GL_LINES)
				glVertex3f(0,0,0)
				glVertex3f(1,0,0)
				glEnd()
				glPopMatrix()
				glPushMatrix()
				glRotate(self.dragEndAngle, 0,-1,0)
				glBegin(GL_LINES)
				glVertex3f(0,0,0)
				glVertex3f(1,0,0)
				glEnd()
				glTranslatef(1.1,0,0)
				glColor4ub(0,0,0,255)
				opengl.glDrawStringCenter("%d" % (abs(self.dragEndAngle - self.dragStartAngle)))
				glColor4ub(255,255,0,255)
				glPopMatrix()
		else:
			glColor4ub(128,128,0,255)
			glLineWidth(1)
		glBegin(GL_LINE_LOOP)
		for i in xrange(0, 64):
			glVertex3f(math.cos(i/32.0*math.pi), 0, math.sin(i/32.0*math.pi))
		glEnd()
		glEnable(GL_DEPTH_TEST)

class toolScale(object):
	def __init__(self, parent):
		self.parent = parent
		self.node = None
		self.scale = None

	def _pointDist(self, p0, p1, p2):
		return numpy.linalg.norm(numpy.cross((p0 - p1), (p0 - p2))) / numpy.linalg.norm(p2 - p1)

	def _traceNodes(self, p0, p1):
		s = self._nodeSize()
		if self._pointDist(numpy.array([0,0,0],numpy.float32), p0, p1) < s * 2:
			return 1
		if self._pointDist(numpy.array([s*15,0,0],numpy.float32), p0, p1) < s * 2:
			return 2
		if self._pointDist(numpy.array([0,s*15,0],numpy.float32), p0, p1) < s * 2:
			return 3
		if self._pointDist(numpy.array([0,0,s*15],numpy.float32), p0, p1) < s * 2:
			return 4
		return None

	def _lineLineCrossingDistOnLine(self, s0, e0, s1, e1):
		d0 = e0 - s0
		d1 = e1 - s1
		a = numpy.dot(d0, d0)
		b = numpy.dot(d0, d1)
		e = numpy.dot(d1, d1)
		d = a*e - b*b

		r = s0 - s1
		c = numpy.dot(d0, r)
		f = numpy.dot(d1, r)

		s = (b*f - c*e) / d
		t = (a*f - b*c) / d
		return t

	def _nodeSize(self):
		return float(self.parent._zoom) / float(self.parent.GetSize().GetWidth()) * 6.0

	def OnMouseMove(self, p0, p1):
		self.node = self._traceNodes(p0, p1)

	def OnDragStart(self, p0, p1):
		if self.node is None:
			return False
		return True

	def OnDrag(self, p0, p1):
		s = self._nodeSize()
		endPoint = [1,1,1]
		if self.node == 2:
			endPoint = [1,0,0]
		elif self.node == 3:
			endPoint = [0,1,0]
		elif self.node == 4:
			endPoint = [0,0,1]
		scale = self._lineLineCrossingDistOnLine(p0, p1, numpy.array([0,0,0], numpy.float32), numpy.array(endPoint, numpy.float32)) / 15.0 / s
		if not wx.GetKeyState(wx.WXK_SHIFT):
			objMatrix = self.parent.getObjectMatrix()
			scaleX = numpy.linalg.norm(objMatrix[::,0].getA().flatten())
			scaleY = numpy.linalg.norm(objMatrix[::,1].getA().flatten())
			scaleZ = numpy.linalg.norm(objMatrix[::,2].getA().flatten())
			if self.node == 1 or not wx.GetKeyState(wx.WXK_CONTROL):
				matrixScale = (scaleX + scaleY + scaleZ) / 3
			elif self.node == 2:
				matrixScale = scaleX
			elif self.node == 3:
				matrixScale = scaleY
			elif self.node == 4:
				matrixScale = scaleZ
			scale = (round((matrixScale * scale) * 10) / 10) / matrixScale
		if scale < 0:
			scale = -scale
		if scale < 0.1:
			scale = 0.1
		self.scale = scale
		if self.node == 1 or not wx.GetKeyState(wx.WXK_CONTROL):
			self.parent.tempMatrix = numpy.matrix([[scale,0,0], [0, scale, 0], [0, 0, scale]], numpy.float64)
		elif self.node == 2:
			self.parent.tempMatrix = numpy.matrix([[scale,0,0], [0, 1, 0], [0, 0, 1]], numpy.float64)
		elif self.node == 3:
			self.parent.tempMatrix = numpy.matrix([[1,0,0], [0, scale, 0], [0, 0, 1]], numpy.float64)
		elif self.node == 4:
			self.parent.tempMatrix = numpy.matrix([[1,0,0], [0, 1, 0], [0, 0, scale]], numpy.float64)

	def OnDragEnd(self):
		self.scale = None

	def OnDraw(self):
		s = self._nodeSize()
		sx = s*15
		sy = s*15
		sz = s*15
		if self.node == 2 and self.scale is not None:
			sx *= self.scale
		if self.node == 3 and self.scale is not None:
			sy *= self.scale
		if self.node == 4 and self.scale is not None:
			sz *= self.scale
		objMatrix = self.parent.getObjectMatrix()
		scaleX = numpy.linalg.norm(objMatrix[::,0].getA().flatten())
		scaleY = numpy.linalg.norm(objMatrix[::,1].getA().flatten())
		scaleZ = numpy.linalg.norm(objMatrix[::,2].getA().flatten())
		if self.scale is not None:
			scaleX *= self.scale
			scaleY *= self.scale
			scaleZ *= self.scale

		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		glColor3ub(0,0,0)
		size = self.parent.getObjectSize()
		radius = self.parent.getObjectBoundaryCircle()
		if self.scale is not None:
			radius *= self.scale
		glPushMatrix()
		glTranslate(0,0,size[2]/2 + 5)
		glRotate(-self.parent._yaw, 0,0,1)
		if self.parent._pitch < 80:
			glTranslate(0, radius + 5,0)
		elif self.parent._pitch < 100:
			glTranslate(0, (radius + 5) * (90 - self.parent._pitch) / 10,0)
		else:
			glTranslate(0,-(radius + 5),0)
		if self.parent.tempMatrix is not None:
			size = (numpy.matrix([size]) * self.parent.tempMatrix).getA().flatten()
		opengl.glDrawStringCenter("W, D, H: %0.1f, %0.1f, %0.1f mm" % (size[0], size[1], size[2]))
		glPopMatrix()

		glLineWidth(1)
		glBegin(GL_LINES)
		glColor3ub(128,0,0)
		glVertex3f(0, 0, 0)
		glVertex3f(sx, 0, 0)
		glColor3ub(0,128,0)
		glVertex3f(0, 0, 0)
		glVertex3f(0, sy, 0)
		glColor3ub(0,0,128)
		glVertex3f(0, 0, 0)
		glVertex3f(0, 0, sz)
		glEnd()

		glLineWidth(2)
		if self.node == 1:
			glColor3ub(255,255,255)
		else:
			glColor3ub(192,192,192)
		opengl.DrawBox([-s,-s,-s], [s,s,s])
		if self.node == 1:
			glColor3ub(0,0,0)
			opengl.glDrawStringCenter("%0.2f" % ((scaleX + scaleY + scaleZ) / 3.0))

		if self.node == 2:
			glColor3ub(255,64,64)
		else:
			glColor3ub(128,0,0)
		glPushMatrix()
		glTranslatef(sx,0,0)
		opengl.DrawBox([-s,-s,-s], [s,s,s])
		if self.node == 2:
			glColor3ub(0,0,0)
			opengl.glDrawStringCenter("%0.2f" % (scaleX))
		glPopMatrix()
		if self.node == 3:
			glColor3ub(64,255,64)
		else:
			glColor3ub(0,128,0)
		glPushMatrix()
		glTranslatef(0,sy,0)
		opengl.DrawBox([-s,-s,-s], [s,s,s])
		if self.node == 3:
			glColor3ub(0,0,0)
			opengl.glDrawStringCenter("%0.2f" % (scaleY))
		glPopMatrix()
		if self.node == 4:
			glColor3ub(64,64,255)
		else:
			glColor3ub(0,0,128)
		glPushMatrix()
		glTranslatef(0,0,sz)
		opengl.DrawBox([-s,-s,-s], [s,s,s])
		if self.node == 4:
			glColor3ub(0,0,0)
			opengl.glDrawStringCenter("%0.2f" % (scaleZ))
		glPopMatrix()

		glEnable(GL_DEPTH_TEST)
		glColor(255,255,255)
		size = size / 2
		size += 0.01
		glLineWidth(1)
		glBegin(GL_LINES)
		glVertex3f(size[0], size[1], size[2])
		glVertex3f(size[0], size[1], size[2]/4*3)
		glVertex3f(size[0], size[1], size[2])
		glVertex3f(size[0], size[1]/4*3, size[2])
		glVertex3f(size[0], size[1], size[2])
		glVertex3f(size[0]/4*3, size[1], size[2])

		glVertex3f(-size[0], size[1], size[2])
		glVertex3f(-size[0], size[1], size[2]/4*3)
		glVertex3f(-size[0], size[1], size[2])
		glVertex3f(-size[0], size[1]/4*3, size[2])
		glVertex3f(-size[0], size[1], size[2])
		glVertex3f(-size[0]/4*3, size[1], size[2])

		glVertex3f(size[0], -size[1], size[2])
		glVertex3f(size[0], -size[1], size[2]/4*3)
		glVertex3f(size[0], -size[1], size[2])
		glVertex3f(size[0], -size[1]/4*3, size[2])
		glVertex3f(size[0], -size[1], size[2])
		glVertex3f(size[0]/4*3, -size[1], size[2])

		glVertex3f(-size[0], -size[1], size[2])
		glVertex3f(-size[0], -size[1], size[2]/4*3)
		glVertex3f(-size[0], -size[1], size[2])
		glVertex3f(-size[0], -size[1]/4*3, size[2])
		glVertex3f(-size[0], -size[1], size[2])
		glVertex3f(-size[0]/4*3, -size[1], size[2])

		glVertex3f(size[0], size[1], -size[2])
		glVertex3f(size[0], size[1], -size[2]/4*3)
		glVertex3f(size[0], size[1], -size[2])
		glVertex3f(size[0], size[1]/4*3, -size[2])
		glVertex3f(size[0], size[1], -size[2])
		glVertex3f(size[0]/4*3, size[1], -size[2])

		glVertex3f(-size[0], size[1], -size[2])
		glVertex3f(-size[0], size[1], -size[2]/4*3)
		glVertex3f(-size[0], size[1], -size[2])
		glVertex3f(-size[0], size[1]/4*3, -size[2])
		glVertex3f(-size[0], size[1], -size[2])
		glVertex3f(-size[0]/4*3, size[1], -size[2])

		glVertex3f(size[0], -size[1], -size[2])
		glVertex3f(size[0], -size[1], -size[2]/4*3)
		glVertex3f(size[0], -size[1], -size[2])
		glVertex3f(size[0], -size[1]/4*3, -size[2])
		glVertex3f(size[0], -size[1], -size[2])
		glVertex3f(size[0]/4*3, -size[1], -size[2])

		glVertex3f(-size[0], -size[1], -size[2])
		glVertex3f(-size[0], -size[1], -size[2]/4*3)
		glVertex3f(-size[0], -size[1], -size[2])
		glVertex3f(-size[0], -size[1]/4*3, -size[2])
		glVertex3f(-size[0], -size[1], -size[2])
		glVertex3f(-size[0]/4*3, -size[1], -size[2])
		glEnd()

		glEnable(GL_DEPTH_TEST)
