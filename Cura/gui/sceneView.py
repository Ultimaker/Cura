from __future__ import absolute_import

import wx
import numpy
import time

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GLU import *
from OpenGL.GL import *

from Cura.util import profile
from Cura.util import meshLoader
from Cura.util import objectScene
from Cura.util import resources
from Cura.gui.util import opengl
from Cura.gui.util import openglGui

class anim(object):
	def __init__(self, start, end, runTime):
		self._start = start
		self._end = end
		self._startTime = time.time()
		self._runTime = runTime

	def isDone(self):
		return time.time() > self._startTime + self._runTime

	def getPosition(self):
		if self.isDone():
			return self._end
		f = (time.time() - self._startTime) / self._runTime
		ts = f*f
		tc = f*f*f
		#f = 6*tc*ts + -15*ts*ts + 10*tc
		f = tc + -3*ts + 3*f
		return self._start + (self._end - self._start) * f

class SceneView(openglGui.glGuiPanel):
	def __init__(self, parent):
		super(SceneView, self).__init__(parent)

		self._yaw = 30
		self._pitch = 60
		self._zoom = 300
		self._scene = objectScene.Scene()
		self._objectShader = None
		self._focusObj = None
		self._selectedObj = None
		self._objColors = [None,None,None,None]
		self._mouseX = -1
		self._mouseY = -1
		self._mouseState = None
		self._viewTarget = numpy.array([0,0,0], numpy.float32)
		self._animView = None
		self._animZoom = None
		self._platformMesh = meshLoader.loadMeshes(resources.getPathForMesh('ultimaker_platform.stl'))[0]
		self._platformMesh._drawOffset = numpy.array([0,0,0.5], numpy.float32)
		wx.EVT_IDLE(self, self.OnIdle)
		self.updateProfileToControls()

	def OnIdle(self, e):
		if self._animView is not None or self._animZoom is not None:
			self.Refresh()
			return
		for obj in self._scene.objects():
			if obj._loadAnim is not None:
				self.Refresh()
				return

	def loadScene(self, fileList):
		for filename in fileList:
			for obj in meshLoader.loadMeshes(filename):
				obj._loadAnim = anim(1, 0, 2)
				self._scene.add(obj)
				self._selectObject(obj)

	def _deleteObject(self, obj):
		if obj == self._selectedObj:
			self._selectedObj = None
		if obj == self._focusObj:
			self._focusObj = None
		self._scene.remove(obj)
		for m in obj._meshList:
			if m.vbo is not None:
				self.glReleaseList.append(m.vbo)

	def _selectObject(self, obj):
		self._selectedObj = obj
		newViewPos = numpy.array([self._selectedObj.getPosition()[0], self._selectedObj.getPosition()[1], self._selectedObj.getMaximum()[2] / 2])
		self._animView = anim(self._viewTarget.copy(), newViewPos, 0.5)
		newZoom = self._selectedObj.getBoundaryCircle() * 6
		self._animZoom = anim(self._zoom, newZoom, 0.5)

	def updateProfileToControls(self):
		self._machineSize = numpy.array([profile.getPreferenceFloat('machine_width'), profile.getPreferenceFloat('machine_depth'), profile.getPreferenceFloat('machine_height')])
		self._objColors[0] = profile.getPreferenceColour('model_colour')
		self._objColors[1] = profile.getPreferenceColour('model_colour2')
		self._objColors[2] = profile.getPreferenceColour('model_colour3')
		self._objColors[3] = profile.getPreferenceColour('model_colour4')
		self._scene.setMachineSize(self._machineSize)

	def OnKeyChar(self, keyCode):
		if keyCode == wx.WXK_DELETE or keyCode == wx.WXK_NUMPAD_DELETE:
			if self._selectedObj is not None:
				self._deleteObject(self._selectedObj)
				self.Refresh()

		if keyCode == wx.WXK_F3:
			shaderEditor(self, self.ShaderUpdate, self._objectLoadShader.getVertexShader(), self._objectLoadShader.getFragmentShader())

	def ShaderUpdate(self, v, f):
		s = opengl.GLShader(v, f)
		if s.isValid():
			self._objectLoadShader.release()
			self._objectLoadShader = s
			self.Refresh()

	def OnMouseDown(self,e):
		self._mouseX = e.GetX()
		self._mouseY = e.GetY()
		self._mouseClick3DPos = self._mouse3Dpos
		if e.ButtonDClick():
			self._mouseState = 'doubleClick'
		else:
			self._mouseState = 'dragOrClick'
		if self._mouseState == 'dragOrClick':
			if e.Button == 1:
				if self._focusObj is not None:
					self._selectedObj = self._focusObj
					self.Refresh()

	def OnMouseUp(self, e):
		if self._mouseState == 'dragOrClick':
			if e.Button == 1:
				if self._focusObj is not None:
					self._selectObject(self._focusObj)
				else:
					self._selectedObj = None
					self.Refresh()
		if self._mouseState == 'drag' and self._selectedObj is not None:
			self._scene.pushFree()
			self.Refresh()
		self._mouseState = None

	def OnMouseMotion(self,e):
		if e.Dragging() and self._mouseState is not None:
			self._mouseState = 'drag'
			if not e.LeftIsDown() and e.RightIsDown():
				self._yaw += e.GetX() - self._mouseX
				self._pitch -= e.GetY() - self._mouseY
				if self._pitch > 170:
					self._pitch = 170
				if self._pitch < 10:
					self._pitch = 10
			elif (e.LeftIsDown() and e.RightIsDown()) or e.MiddleIsDown():
				self._zoom += e.GetY() - self._mouseY
				if self._zoom < 1:
					self._zoom = 1
				if self._zoom > numpy.max(self._machineSize) * 3:
					self._zoom = numpy.max(self._machineSize) * 3
			elif e.LeftIsDown() and self._selectedObj is not None:
				z = max(0, self._mouseClick3DPos[2])
				p0 = opengl.unproject(self._mouseX, self.viewport[1] + self.viewport[3] - self._mouseY, 0, self.modelMatrix, self.projMatrix, self.viewport)
				p1 = opengl.unproject(self._mouseX, self.viewport[1] + self.viewport[3] - self._mouseY, 1, self.modelMatrix, self.projMatrix, self.viewport)
				p2 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 0, self.modelMatrix, self.projMatrix, self.viewport)
				p3 = opengl.unproject(e.GetX(), self.viewport[1] + self.viewport[3] - e.GetY(), 1, self.modelMatrix, self.projMatrix, self.viewport)
				p0[2] -= z
				p1[2] -= z
				p2[2] -= z
				p3[2] -= z
				cursorZ0 = p0 - (p1 - p0) * (p0[2] / (p1[2] - p0[2]))
				cursorZ1 = p2 - (p3 - p2) * (p2[2] / (p3[2] - p2[2]))
				diff = cursorZ1 - cursorZ0
				self._selectedObj.setPosition(self._selectedObj.getPosition() + diff[0:2])

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
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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
		if self._animView is not None:
			self._viewTarget = self._animView.getPosition()
			if self._animView.isDone():
				self._animView = None
		if self._animZoom is not None:
			self._zoom = self._animZoom.getPosition()
			if self._animZoom.isDone():
				self._animZoom = None
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
			self._objectLoadShader = opengl.GLShader("""
uniform float cameraDistance;
uniform float intensity;
uniform float scale;
varying float light_amount;

void main(void)
{
	vec4 tmp = gl_Vertex;
    tmp.x += sin(tmp.z/5+intensity*30) * scale * intensity;
    tmp.y += sin(tmp.z/3+intensity*40) * scale * intensity;
    gl_Position = gl_ModelViewProjectionMatrix * tmp;
    gl_FrontColor = gl_Color;

	light_amount = abs(dot(normalize(gl_NormalMatrix * gl_Normal), normalize(gl_LightSource[0].position.xyz)));
	light_amount *= 1 - (length(gl_Position.xyz - vec3(0,0,cameraDistance)) / 1.5 / cameraDistance);
	light_amount += 0.2;
}
			""","""
uniform float cameraDistance;
uniform float intensity;
varying float light_amount;

void main(void)
{
	gl_FragColor = vec4(gl_Color.xyz * light_amount, 1-intensity);
}
			""")
		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		self.viewport = glGetIntegerv(GL_VIEWPORT)
		self.modelMatrix = glGetDoublev(GL_MODELVIEW_MATRIX)
		self.projMatrix = glGetDoublev(GL_PROJECTION_MATRIX)

		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

		for n in xrange(0, len(self._scene.objects())):
			obj = self._scene.objects()[n]
			glColor4ub((n >> 24) & 0xFF, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF)
			self._renderObject(obj)

		if self._mouseX > -1:
			n = glReadPixels(self._mouseX, self.GetSize().GetHeight() - 1 - self._mouseY, 1, 1, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8)[0][0]
			if n < len(self._scene.objects()):
				self._focusObj = self._scene.objects()[n]
			else:
				self._focusObj = None
			f = glReadPixels(self._mouseX, self.GetSize().GetHeight() - 1 - self._mouseY, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[0][0]
			self._mouse3Dpos = opengl.unproject(self._mouseX, self.viewport[1] + self.viewport[3] - self._mouseY, f, self.modelMatrix, self.projMatrix, self.viewport)

		self._init3DView()
		glTranslate(0,0,-self._zoom)
		glRotate(-self._pitch, 1,0,0)
		glRotate(self._yaw, 0,0,1)
		glTranslate(-self._viewTarget[0],-self._viewTarget[1],-self._viewTarget[2])

		glStencilFunc(GL_ALWAYS, 1, 1)
		glStencilOp(GL_INCR, GL_INCR, GL_INCR)
		self._objectShader.bind()
		self._objectShader.setUniform('cameraDistance', self._zoom)
		for obj in self._scene.objects():
			if obj._loadAnim is not None:
				if obj._loadAnim.isDone():
					obj._loadAnim = None
				else:
					continue
			col = self._objColors[0]
			if not self._scene.checkPlatform(obj):
				col = [0.5,0.5,0.5,0.8]
			glDisable(GL_STENCIL_TEST)
			if self._selectedObj == obj:
				col = map(lambda n: n * 1.5, col)
				glEnable(GL_STENCIL_TEST)
			elif self._focusObj == obj:
				col = map(lambda n: n * 1.2, col)
			elif self._focusObj is not None or  self._selectedObj is not None:
				col = map(lambda n: n * 0.8, col)
			glColor4f(col[0], col[1], col[2], col[3])
			self._renderObject(obj)
		self._objectShader.unbind()

		glDisable(GL_STENCIL_TEST)
		glEnable(GL_BLEND)
		self._objectLoadShader.bind()
		self._objectLoadShader.setUniform('cameraDistance', self._zoom)
		glColor4f(0.2, 0.6, 1.0, 1.0)
		for obj in self._scene.objects():
			if obj._loadAnim is None:
				continue
			self._objectLoadShader.setUniform('intensity', obj._loadAnim.getPosition())
			self._objectLoadShader.setUniform('scale', obj.getBoundaryCircle() / 20)
			self._renderObject(obj)
		self._objectLoadShader.unbind()
		glDisable(GL_BLEND)

		self._drawMachine()

		#Draw the outline of the selected object, on top of everything else except the GUI.
		if self._selectedObj is not None and self._selectedObj._loadAnim is None:
			glDisable(GL_DEPTH_TEST)
			glEnable(GL_CULL_FACE)
			glEnable(GL_STENCIL_TEST)
			glStencilFunc(GL_EQUAL, 0, 255)
			glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
			glLineWidth(2)
			glColor4f(1,1,1,0.5)
			self._renderObject(self._selectedObj)
			glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
			glDisable(GL_STENCIL_TEST)
			glDisable(GL_CULL_FACE)
			glEnable(GL_DEPTH_TEST)

	def _renderObject(self, obj):
		glPushMatrix()
		glTranslate(obj.getPosition()[0], obj.getPosition()[1], 0)
		offset = obj.getDrawOffset()
		glTranslate(-offset[0], -offset[1], -offset[2])
		for m in obj._meshList:
			if m.vbo is None:
				m.vbo = opengl.GLVBO(m.vertexes, m.normal)
			m.vbo.render()
		glPopMatrix()

	def _drawMachine(self):
		glEnable(GL_CULL_FACE)
		glEnable(GL_BLEND)

		if profile.getPreference('machine_type') == 'ultimaker':
			glColor4f(1,1,1,0.5)
			self._objectShader.bind()
			self._objectShader.setUniform('cameraDistance', self._zoom)
			self._renderObject(self._platformMesh)
			self._objectShader.unbind()

		size = [profile.getPreferenceFloat('machine_width'), profile.getPreferenceFloat('machine_depth'), profile.getPreferenceFloat('machine_height')]
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

		glDisableClientState(GL_VERTEX_ARRAY)
		glDisable(GL_BLEND)
		glDisable(GL_CULL_FACE)

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
