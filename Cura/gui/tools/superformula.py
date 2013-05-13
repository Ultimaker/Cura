from __future__ import absolute_import

import wx
import math
import time
import random
import numpy

from wx import glcanvas
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLU import *

from Cura.gui.util import opengl
from Cura.util import mesh

class superShape(object):
	def __init__(self, a1, b1, m1, n11, n21, n31, a2, b2, m2, n12, n22, n32):
		self._a1 = a1
		self._b1 = b1
		self._m1 = math.floor(m1)
		self._n11 = n11
		self._n21 = n21
		self._n31 = n31
		self._a2 = a2
		self._b2 = b2
		self._m2 = m2
		self._n12 = n12
		self._n22 = n22
		self._n32 = n32

		points = []
		cnt = 64
		for n in xrange(-cnt, cnt):
			row = []
			points.append(row)
			f1 = n * math.pi / cnt
			try:
				r1 = math.pow((math.pow(abs(math.cos(m1*f1/4)/a1),n21) + math.pow(abs(math.sin(m1*f1/4)/b1), n31)), -(1/n11))
			except:
				r1 = 1.0
			for m in xrange(0, cnt):
				f2 = m * math.pi / ((cnt*2) - 2)
				try:
					r2 = math.pow((math.pow(abs(math.cos(m2*f2/4)/a2),n22) + math.pow(abs(math.sin(m2*f2/4)/b2), n32)), -(1/n12))
				except:
					r2 = 1.0

				x = r1 * math.cos(f1) * r2 * math.cos(f2)
				y = r1 * math.sin(f1) * r2 * math.cos(f2)
				z = r2 * math.sin(f2)

				row.append([x,y,z])

		self._obj = mesh.printableObject()
		objMesh = self._obj._addMesh()
		objMesh._prepareFaceCount(len(points) * (len(points[0]) - 1) * 2)

		for n in xrange(-1, len(points) - 1):
			row1 = points[n]
			row2 = points[n+1]
			for m in xrange(0, len(row1) - 1):
				p0 = row1[m]
				p1 = row1[m+1]
				p2 = row2[m]
				p3 = row2[m+1]

				objMesh._addFace(p0[0], p0[1], p0[2], p2[0], p2[1], p2[2], p1[0], p1[1], p1[2])
				objMesh._addFace(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], p3[0], p3[1], p3[2])

		self._obj._postProcessAfterLoad()

	def isValid(self):
		size = self._obj.getSize()
		if size[0] / size[2] > 10:
			return False
		return True

	def draw(self):
		for m in self._obj._meshList:
			if m.vbo is None:
				m.vbo = opengl.GLVBO(m.vertexes, m.normal)
			m.vbo.render()

class superformulaEvolver(wx.Frame):
	def __init__(self, parent):
		super(superformulaEvolver, self).__init__(parent, title='Cura - Superformula')
		self._rotate = 0.0
		self._t0 = time.time()

		sizer = wx.BoxSizer()
		self.SetSizer(sizer)

		attribList = (glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 32, glcanvas.WX_GL_STENCIL_SIZE, 8)
		self._glCanvas = glcanvas.GLCanvas(self, style=wx.WANTS_CHARS, attribList = attribList)
		self._glCanvas.SetMinSize((800,600))
		sizer.Add(self._glCanvas, 1, flag=wx.EXPAND)
		self._context = glcanvas.GLContext(self._glCanvas)

		wx.EVT_PAINT(self._glCanvas, self._OnPaint)
		wx.EVT_SIZE(self._glCanvas, self._OnSize)
		wx.EVT_ERASE_BACKGROUND(self._glCanvas, self._OnEraseBackground)
		wx.EVT_IDLE(self, self._OnIdle)

		wx.EVT_LEFT_DOWN(self._glCanvas, self._OnMouseDown)

		self._shapes = [None] * 12
		self._releaseList = []

		self._randomize()

		self.Maximize()

	def _OnMouseDown(self, e):
		size = self._glCanvas.GetSize()
		sel = e.GetX() / (size.GetWidth() / 4) + (size.GetHeight() - e.GetY()) / (size.GetHeight() / 3) * 4
		shape = self._shapes[sel]
		for n in xrange(0, len(self._shapes)):
			if n == sel:
				continue
			for m in self._shapes[n]._obj._meshList:
				if m.vbo is not None:
					self._releaseList.append(m.vbo)
			f = 0.5 + n * 0.1
			update = True
			while update:
				self._shapes[n] = superShape(
					shape._a1 + random.uniform(-f, f) / 2.0,
					shape._b1 + random.uniform(-f, f) / 2.0,
					shape._m1 + random.uniform(-f, f) * 2.0,
					shape._n11 + random.uniform(-f, f),
					shape._n21 + random.uniform(-f, f),
					shape._n31 + random.uniform(-f, f),
					shape._a2 + random.uniform(-f, f) / 2.0,
					shape._b2 + random.uniform(-f, f) / 2.0,
					shape._m2 + random.uniform(-f, f),
					shape._n12 + random.uniform(-f, f),
					shape._n22 + random.uniform(-f, f),
					shape._n32 + random.uniform(-f, f))
				update = not self._shapes[n].isValid()

	def _randomize(self):
		for shape in self._shapes:
			if shape is not None:
				for m in shape._obj._meshList:
					if m.vbo is not None:
						self._releaseList.append(m.vbo)
		for n in xrange(0, len(self._shapes)):
			update = True
			while update:
				self._shapes[n] = superShape(
					random.uniform(0.5, 5.0),
					random.uniform(0.5, 5.0),
					random.uniform(0.5, 20.0),
					random.uniform(0.5, 10.0),
					random.uniform(0.5, 10.0),
					random.uniform(0.5, 10.0),
					random.uniform(0.5, 5.0),
					random.uniform(0.5, 5.0),
					random.uniform(0.5, 10.0),
					random.uniform(0.5, 10.0),
					random.uniform(0.5, 10.0),
					random.uniform(0.5, 10.0))
				update = not self._shapes[n].isValid()

	def _OnEraseBackground(self,event):
		#Workaround for windows background redraw flicker.
		pass

	def _OnSize(self, e):
		self.Refresh()

	def _OnIdle(self, e):
		self._glCanvas.Refresh()

	def _OnPaint(self, e):
		dc = wx.PaintDC(self._glCanvas)

		self._glCanvas.SetCurrent(self._context)
		for obj in self._releaseList:
			obj.release()
		self._releaseList = []

		size = self._glCanvas.GetSize()
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

		glClearColor(0.0, 0.0, 0.0, 1.0)
		glClearStencil(0)
		glClearDepth(1.0)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		aspect = float(size.GetWidth()) / float(size.GetHeight())
		gluPerspective(30.0, aspect, 1.0, 1000.0)

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

		glTranslate(0,0,-2.0)
		glRotate(-45 - math.sin(self._rotate/50.0) * 30, 1, 0, 0)
		glRotate(self._rotate, 0, 0, 1)
		self._rotate += (self._t0 - time.time()) * 20
		self._t0 = time.time()

		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glLightfv(GL_LIGHT0, GL_POSITION, [0.2, 0.2, 1.0, 0.0])
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8,1.0,0.8,0])
		glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3,0.3,0.3,0])
		glEnable(GL_LIGHT1)
		glLightfv(GL_LIGHT1, GL_POSITION, [1.2, 0.2, 0.2, 0.0])
		glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.5,0.3,0.2,0])
		glLightfv(GL_LIGHT1, GL_AMBIENT, [0.0,0.0,0.0,0])

		for n in xrange(0, len(self._shapes)):
			shape = self._shapes[n]
			scale = 1.0/numpy.max(shape._obj.getSize())
			glPushMatrix()
			glScalef(scale, scale, scale)
			glEnable(GL_NORMALIZE)
			glViewport(size.GetWidth() / 4 * (n % 4), size.GetHeight() / 3 * (n / 4), size.GetWidth() / 4, size.GetHeight() / 3)
			shape.draw()
			glPopMatrix()

		glFlush()
		self._glCanvas.SwapBuffers()

class superformulaWindow(wx.Frame):
	def __init__(self, parent):
		super(superformulaWindow, self).__init__(parent, title='Cura - Superformula')
		self._rotate = 0.0
		self._t0 = time.time()

		self.panel = wx.Panel(self, -1)
		self.SetSizer(wx.BoxSizer())
		self.GetSizer().Add(self.panel, 1, wx.EXPAND)

		sizer = wx.GridBagSizer(2, 2)

		sizer.Add(wx.StaticText(self.panel, -1, 'A1'), pos=(0,0))
		self.sliderA1 = wx.Slider(self.panel, -1, 10, 5, 50, size=(150, -1))
		sizer.Add(self.sliderA1, pos=(0,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'B1'), pos=(1,0))
		self.sliderB1 = wx.Slider(self.panel, -1, 10, 5, 50, size=(150, -1))
		sizer.Add(self.sliderB1, pos=(1,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'M1'), pos=(2,0))
		self.sliderM1 = wx.Slider(self.panel, -1, 50, 5, 200, size=(150, -1))
		sizer.Add(self.sliderM1, pos=(2,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'N11'), pos=(3,0))
		self.sliderN11 = wx.Slider(self.panel, -1, 20, 5, 100, size=(150, -1))
		sizer.Add(self.sliderN11, pos=(3,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'N21'), pos=(4,0))
		self.sliderN21 = wx.Slider(self.panel, -1, 20, 5, 100, size=(150, -1))
		sizer.Add(self.sliderN21, pos=(4,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'N31'), pos=(5,0))
		self.sliderN31 = wx.Slider(self.panel, -1, 20, 5, 100, size=(150, -1))
		sizer.Add(self.sliderN31, pos=(5,1))

		sizer.Add(wx.StaticText(self.panel, -1, 'A2'), pos=(6,0))
		self.sliderA2 = wx.Slider(self.panel, -1, 10, 5, 50, size=(150, -1))
		sizer.Add(self.sliderA2, pos=(6,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'B2'), pos=(7,0))
		self.sliderB2 = wx.Slider(self.panel, -1, 10, 5, 50, size=(150, -1))
		sizer.Add(self.sliderB2, pos=(7,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'M2'), pos=(8,0))
		self.sliderM2 = wx.Slider(self.panel, -1, 20, 5, 100, size=(150, -1))
		sizer.Add(self.sliderM2, pos=(8,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'N12'), pos=(9,0))
		self.sliderN12 = wx.Slider(self.panel, -1, 20, 5, 100, size=(150, -1))
		sizer.Add(self.sliderN12, pos=(9,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'N22'), pos=(10,0))
		self.sliderN22 = wx.Slider(self.panel, -1, 20, 5, 100, size=(150, -1))
		sizer.Add(self.sliderN22, pos=(10,1))
		sizer.Add(wx.StaticText(self.panel, -1, 'N32'), pos=(11,0))
		self.sliderN32 = wx.Slider(self.panel, -1, 20, 5, 100, size=(150, -1))
		sizer.Add(self.sliderN32, pos=(11,1))

		self.randomButton = wx.Button(self.panel, -1, 'Randomize')
		sizer.Add(self.randomButton, pos=(12,1))
		self.addButton = wx.Button(self.panel, -1, 'Add to print')
		sizer.Add(self.addButton, pos=(13,1))

		attribList = (glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 32, glcanvas.WX_GL_STENCIL_SIZE, 8)
		self._glCanvas = glcanvas.GLCanvas(self.panel, style=wx.WANTS_CHARS, attribList = attribList)
		self._glCanvas.SetMinSize((800,600))
		sizer.Add(self._glCanvas, pos=(0,2), span=(14,1), flag=wx.EXPAND)
		self._context = glcanvas.GLContext(self._glCanvas)

		sizer.AddGrowableRow(13)
		sizer.AddGrowableCol(2)
		self.panel.SetSizer(sizer)
		self.Layout()
		self.Fit()

		wx.EVT_PAINT(self._glCanvas, self._OnPaint)
		wx.EVT_SIZE(self._glCanvas, self._OnSize)
		wx.EVT_ERASE_BACKGROUND(self._glCanvas, self._OnEraseBackground)
		wx.EVT_IDLE(self, self._OnIdle)

		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderA1)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderB1)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderM1)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderN11)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderN21)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderN31)

		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderA2)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderB2)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderM2)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderN12)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderN22)
		self.Bind(wx.EVT_SLIDER, lambda e: self._updateShape(), self.sliderN32)

		self.Bind(wx.EVT_BUTTON, lambda e: self.onRandom(), self.randomButton)
		self.Bind(wx.EVT_BUTTON, lambda e: self.onAdd(), self.addButton)

		self._shape = None
		self._releaseList = []
		self._updateShape()

	def onRandom(self):
		update = True
		while update:
			update = False
			self.sliderA1.SetValue(random.randint(self.sliderA1.GetMin(), self.sliderA1.GetMax()))
			self.sliderB1.SetValue(random.randint(self.sliderB1.GetMin(), self.sliderB1.GetMax()))
			self.sliderM1.SetValue(random.randint(self.sliderM1.GetMin(), self.sliderM1.GetMax()))
			self.sliderN11.SetValue(random.randint(self.sliderN11.GetMin(), self.sliderN11.GetMax()))
			self.sliderN21.SetValue(random.randint(self.sliderN21.GetMin(), self.sliderN21.GetMax()))
			self.sliderN31.SetValue(random.randint(self.sliderN31.GetMin(), self.sliderN31.GetMax()))
			self.sliderA2.SetValue(random.randint(self.sliderA2.GetMin(), self.sliderA2.GetMax()))
			self.sliderB2.SetValue(random.randint(self.sliderB2.GetMin(), self.sliderB2.GetMax()))
			self.sliderM2.SetValue(random.randint(self.sliderM2.GetMin(), self.sliderM2.GetMax()))
			self.sliderN12.SetValue(random.randint(self.sliderN12.GetMin(), self.sliderN12.GetMax()))
			self.sliderN22.SetValue(random.randint(self.sliderN22.GetMin(), self.sliderN22.GetMax()))
			self.sliderN32.SetValue(random.randint(self.sliderN32.GetMin(), self.sliderN32.GetMax()))
			self._updateShape()
			if not self._shape.isValid():
				update = True

	def onAdd(self):
		scale = 1.0/numpy.max(self._shape._obj.getSize()) * 50

		obj = mesh.printableObject()
		m = obj._addMesh()
		m._prepareFaceCount(self._shape._obj._meshList[0].vertexCount / 3)
		m.vertexes = self._shape._obj._meshList[0].vertexes * scale
		m.vertexCount = self._shape._obj._meshList[0].vertexCount
		obj._postProcessAfterLoad()
		self.GetParent().scene._scene.add(obj)

	def _updateShape(self):
		if self._shape is not None:
			for m in self._shape._obj._meshList:
				if m.vbo is not None:
					self._releaseList.append(m.vbo)
		self._shape = superShape(
			float(self.sliderA1.GetValue()) / 10.0,
			float(self.sliderB1.GetValue()) / 10.0,
			float(self.sliderM1.GetValue()) / 10.0,

			float(self.sliderN11.GetValue()) / 10.0,
			float(self.sliderN21.GetValue()) / 10.0,
			float(self.sliderN31.GetValue()) / 10.0,

			float(self.sliderA2.GetValue()) / 10.0,
			float(self.sliderB2.GetValue()) / 10.0,
			float(self.sliderM2.GetValue()) / 10.0,

			float(self.sliderN12.GetValue()) / 10.0,
			float(self.sliderN22.GetValue()) / 10.0,
			float(self.sliderN32.GetValue()) / 10.0,
		)

	def _OnEraseBackground(self,event):
		#Workaround for windows background redraw flicker.
		pass

	def _OnSize(self, e):
		self.Refresh()

	def _OnIdle(self, e):
		self._glCanvas.Refresh()

	def _OnPaint(self, e):
		dc = wx.PaintDC(self._glCanvas)

		self._glCanvas.SetCurrent(self._context)
		for obj in self._releaseList:
			obj.release()
		self._releaseList = []

		size = self._glCanvas.GetSize()
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

		glClearColor(0.0, 0.0, 0.0, 1.0)
		glClearStencil(0)
		glClearDepth(1.0)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		aspect = float(size.GetWidth()) / float(size.GetHeight())
		gluPerspective(45.0, aspect, 1.0, 1000.0)

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

		glTranslate(0,0,-2)
		glRotate(-45 - math.sin(self._rotate/50.0) * 30, 1, 0, 0)
		glRotate(self._rotate, 0, 0, 1)
		self._rotate += (self._t0 - time.time()) * 20
		self._t0 = time.time()

		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glLightfv(GL_LIGHT0, GL_POSITION, [0.2, 0.2, 1.0, 0.0])
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8,1.0,0.8,0])
		glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3,0.3,0.3,0])
		glEnable(GL_LIGHT1)
		glLightfv(GL_LIGHT1, GL_POSITION, [1.2, 0.2, 0.2, 0.0])
		glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.5,0.3,0.2,0])
		glLightfv(GL_LIGHT1, GL_AMBIENT, [0.0,0.0,0.0,0])

		scale = 1.0/numpy.max(self._shape._obj.getSize())
		glScalef(scale, scale, scale)
		glEnable(GL_NORMALIZE)

		self._shape.draw()

		glFlush()
		self._glCanvas.SwapBuffers()
