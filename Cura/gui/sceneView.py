from __future__ import absolute_import
from __future__ import division

import numpy
from ctypes import c_void_p

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
		self._objColors = [None,None,None,None]
		self._tmpVertex = None
		self.updateProfileToControls()

	def loadScene(self, fileList):
		for filename in fileList:
			for obj in meshLoader.loadMeshes(filename):
				self._objectList.append(obj)

	def updateProfileToControls(self):
		self._objColors[0] = profile.getPreferenceColour('model_colour')
		self._objColors[1] = profile.getPreferenceColour('model_colour2')
		self._objColors[2] = profile.getPreferenceColour('model_colour3')
		self._objColors[3] = profile.getPreferenceColour('model_colour4')

	def OnMouseMotion(self,e):
		if e.Dragging() and e.LeftIsDown():
			self._yaw += e.GetX() - self.oldX
			self._pitch -= e.GetY() - self.oldY
			if self._pitch > 170:
				self._pitch = 170
			if self._pitch < 10:
				self._pitch = 10
		if e.Dragging() and e.RightIsDown():
			self._zoom += e.GetY() - self.oldY
			if self._zoom < 1:
				self._zoom = 1
			if self._zoom > 500:
				self._zoom = 500
		self.oldX = e.GetX()
		self.oldY = e.GetY()

	def _init3DView(self):
		# set viewing projection
		size = self.GetSize()
		glViewport(0, 0, size.GetWidth(), size.GetHeight())

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
	gl_FragColor = gl_Color * light_amount;
}
			""")
		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(0,0,-15)
		glColor3f(self._objColors[0][0], self._objColors[0][1], self._objColors[0][2])

		self._objectShader.bind()
		self._objectShader.setUniform('cameraDistance', self._zoom)
		if self._tmpVertex is None:
			for obj in self._objectList:
				for m in obj._meshList:
					self._tmpVertex = opengl.GLVBO(m.vertexes, m.normal)

		self._tmpVertex.render()
		self._objectShader.unbind()
