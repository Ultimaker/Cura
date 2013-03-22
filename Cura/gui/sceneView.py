from __future__ import absolute_import
from __future__ import division

import wx

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.util import profile
from Cura.util import meshLoader
from Cura.gui.util import opengl
from Cura.gui.util import openglGui

class SceneView(openglGui.glGuiPanel):
	def __init__(self, parent):
		super(SceneView, self).__init__(parent)

		self._yaw = 30
		self._pitch = 60
		self._zoom = 100
		self._objectList = []
		self._objectShader = None
		self._focusObj = None
		self._selectedObj = None
		self._objColors = [None,None,None,None]
		self._mouseX = -1
		self._mouseY = -1
		self.updateProfileToControls()

	def loadScene(self, fileList):
		for filename in fileList:
			for obj in meshLoader.loadMeshes(filename):
				self._objectList.append(obj)

	def _deleteObject(self, obj):
		if obj == self._selectedObj:
			self._selectedObj = None
		if obj == self._focusObj:
			self._focusObj = None
		self._objectList.remove(obj)
		for m in obj._meshList:
			if m.vbo is not None:
				self.glReleaseList.append(m.vbo)

	def updateProfileToControls(self):
		self._objColors[0] = profile.getPreferenceColour('model_colour')
		self._objColors[1] = profile.getPreferenceColour('model_colour2')
		self._objColors[2] = profile.getPreferenceColour('model_colour3')
		self._objColors[3] = profile.getPreferenceColour('model_colour4')

	def OnKeyChar(self, keyCode):
		if keyCode == wx.WXK_DELETE or keyCode == wx.WXK_NUMPAD_DELETE:
			if self._selectedObj is not None:
				self._deleteObject(self._selectedObj)
				self.Refresh()

	def OnMouseDown(self,e):
		if self._focusObj is not None:
			self._selectedObj = self._focusObj

	def OnMouseMotion(self,e):
		if e.Dragging() and e.LeftIsDown():
			self._yaw += e.GetX() - self._mouseX
			self._pitch -= e.GetY() - self._mouseY
			if self._pitch > 170:
				self._pitch = 170
			if self._pitch < 10:
				self._pitch = 10
		if e.Dragging() and e.RightIsDown():
			self._zoom += e.GetY() - self._mouseY
			if self._zoom < 1:
				self._zoom = 1
			if self._zoom > 500:
				self._zoom = 500
		self._mouseX = e.GetX()
		self._mouseY = e.GetY()

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

		glClearColor(0.8, 0.8, 0.8, 1.0)
		glClearStencil(0)
		glClearDepth(1.0)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		aspect = float(size.GetWidth()) / float(size.GetHeight())
		gluPerspective(45.0, aspect, 1.0, 1000.0)

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

	def OnPaint(self,e):
		if self._objectShader is None:
			self._objectShader = opengl.GLShader("""
uniform float cameraDistance;
varying float light_amount;

void main(void)
{
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount *= 1 - (length(gl_Position.xyz - vec3(0,0,cameraDistance)) / 1.5 / cameraDistance);
	light_amount += 0.2;
}
			""","""
uniform float cameraDistance;
varying float light_amount;

void main(void)
{
	gl_FragColor = vec4(gl_Color.xyz * light_amount, gl_Color[3]);
}
			""")
		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(0,0,-15)
		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

		for n in xrange(0, len(self._objectList)):
			obj = self._objectList[n]
			glColor4ub((n >> 24) & 0xFF, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF)
			self._renderObject(obj)

		if self._mouseX > -1:
			n = glReadPixels(self._mouseX, self.GetSize().GetHeight() - 1 - self._mouseY, 1, 1, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8)[0][0]
			if n < len(self._objectList):
				self._focusObj = self._objectList[n]
			else:
				self._focusObj = None

		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(0,0,-15)

		self._objectShader.bind()
		self._objectShader.setUniform('cameraDistance', self._zoom)
		for obj in self._objectList:
			col = self._objColors[0]
			if self._selectedObj == obj:
				col = map(lambda n: n * 1.5, col)
			elif self._focusObj == obj:
				col = map(lambda n: n * 1.2, col)
			elif self._focusObj is not None or  self._selectedObj is not None:
				col = map(lambda n: n * 0.8, col)
			glColor4f(col[0], col[1], col[2], col[3])
			self._renderObject(obj)
		self._objectShader.unbind()

	def _renderObject(self, obj):
		glPushMatrix()
		offset = (obj.getMinimum() + obj.getMaximum()) / 2
		glTranslate(-offset[0], -offset[1], -obj.getMinimum()[2])
		for m in obj._meshList:
			if m.vbo is None:
				m.vbo = opengl.GLVBO(m.vertexes, m.normal)
			m.vbo.render()
		glPopMatrix()
