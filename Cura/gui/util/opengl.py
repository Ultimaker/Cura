from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import numpy
import wx
import time

from Cura.util import meshLoader
from Cura.util import util3d
from Cura.util import profile
from Cura.util.resources import getPathForMesh, getPathForImage

import OpenGL

OpenGL.ERROR_CHECKING = False
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.GL import shaders
glutInit()

platformMesh = None

class GLReferenceCounter(object):
	def __init__(self):
		self._refCounter = 1

	def incRef(self):
		self._refCounter += 1

	def decRef(self):
		self._refCounter -= 1
		return self._refCounter <= 0

def hasShaderSupport():
	if bool(glCreateShader):
		return True
	return False

class GLShader(GLReferenceCounter):
	def __init__(self, vertexProgram, fragmentProgram):
		super(GLShader, self).__init__()
		self._vertexString = vertexProgram
		self._fragmentString = fragmentProgram
		try:
			vertexShader = shaders.compileShader(vertexProgram, GL_VERTEX_SHADER)
			fragmentShader = shaders.compileShader(fragmentProgram, GL_FRAGMENT_SHADER)

			#shader.compileProgram tries to return the shader program as a overloaded int. But the return value of a shader does not always fit in a int (needs to be a long). So we do raw OpenGL calls.
			# self._program = shaders.compileProgram(self._vertexProgram, self._fragmentProgram)
			self._program = glCreateProgram()
			glAttachShader(self._program, vertexShader)
			glAttachShader(self._program, fragmentShader)
			glLinkProgram(self._program)
			# Validation has to occur *after* linking
			glValidateProgram(self._program)
			if glGetProgramiv(self._program, GL_VALIDATE_STATUS) == GL_FALSE:
				raise RuntimeError("Validation failure: %s"%(glGetProgramInfoLog(self._program)))
			if glGetProgramiv(self._program, GL_LINK_STATUS) == GL_FALSE:
				raise RuntimeError("Link failure: %s" % (glGetProgramInfoLog(self._program)))
			glDeleteShader(vertexShader)
			glDeleteShader(fragmentShader)
		except RuntimeError, e:
			print str(e)
			self._program = None

	def bind(self):
		if self._program is not None:
			shaders.glUseProgram(self._program)

	def unbind(self):
		shaders.glUseProgram(0)

	def release(self):
		if self._program is not None:
			glDeleteProgram(self._program)
			self._program = None

	def setUniform(self, name, value):
		if self._program is not None:
			if type(value) is float:
				glUniform1f(glGetUniformLocation(self._program, name), value)
			elif type(value) is numpy.matrix:
				glUniformMatrix3fv(glGetUniformLocation(self._program, name), 1, False, value.getA().astype(numpy.float32))
			else:
				print 'Unknown type for setUniform: %s' % (str(type(value)))

	def isValid(self):
		return self._program is not None

	def getVertexShader(self):
		return self._vertexString

	def getFragmentShader(self):
		return self._fragmentString

	def __del__(self):
		if self._program is not None and bool(glDeleteProgram):
			print "Shader was not properly released!"

#A Class that acts as an OpenGL shader, but in reality is not none.
class GLFakeShader(GLReferenceCounter):
	def __init__(self):
		super(GLFakeShader, self).__init__()

	def bind(self):
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_COLOR_MATERIAL)
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [1,1,1,1])
		glLightfv(GL_LIGHT0, GL_AMBIENT, [0,0,0,0])
		glLightfv(GL_LIGHT0, GL_SPECULAR, [0,0,0,0])

	def unbind(self):
		glDisable(GL_LIGHTING)

	def release(self):
		pass

	def setUniform(self, name, value):
		pass

	def isValid(self):
		return True

	def getVertexShader(self):
		return ''

	def getFragmentShader(self):
		return ''

class GLVBO(GLReferenceCounter):
	def __init__(self, vertexArray, normalArray = None):
		super(GLVBO, self).__init__()
		if not bool(glGenBuffers):
			self._vertexArray = vertexArray
			self._normalArray = normalArray
			self._size = len(vertexArray)
			self._buffer = None
			self._hasNormals = self._normalArray is not None
		else:
			self._buffer = glGenBuffers(1)
			self._size = len(vertexArray)
			self._hasNormals = normalArray is not None
			glBindBuffer(GL_ARRAY_BUFFER, self._buffer)
			if self._hasNormals:
				glBufferData(GL_ARRAY_BUFFER, numpy.concatenate((vertexArray, normalArray), 1), GL_STATIC_DRAW)
			else:
				glBufferData(GL_ARRAY_BUFFER, vertexArray, GL_STATIC_DRAW)
			glBindBuffer(GL_ARRAY_BUFFER, 0)

	def render(self, render_type = GL_TRIANGLES):
		glEnableClientState(GL_VERTEX_ARRAY)
		if self._buffer is None:
			glVertexPointer(3, GL_FLOAT, 0, self._vertexArray)
			if self._hasNormals:
				glEnableClientState(GL_NORMAL_ARRAY)
				glNormalPointer(GL_FLOAT, 0, self._normalArray)
		else:
			glBindBuffer(GL_ARRAY_BUFFER, self._buffer)
			if self._hasNormals:
				glEnableClientState(GL_NORMAL_ARRAY)
				glVertexPointer(3, GL_FLOAT, 2*3*4, c_void_p(0))
				glNormalPointer(GL_FLOAT, 2*3*4, c_void_p(3 * 4))
			else:
				glVertexPointer(3, GL_FLOAT, 3*4, c_void_p(0))

		batchSize = 996    #Warning, batchSize needs to be dividable by 4, 3 and 2
		extraStartPos = int(self._size / batchSize) * batchSize
		extraCount = self._size - extraStartPos

		for i in xrange(0, int(self._size / batchSize)):
			glDrawArrays(render_type, i * batchSize, batchSize)
		glDrawArrays(render_type, extraStartPos, extraCount)
		if self._buffer is not None:
			glBindBuffer(GL_ARRAY_BUFFER, 0)

		glDisableClientState(GL_VERTEX_ARRAY)
		if self._hasNormals:
			glDisableClientState(GL_NORMAL_ARRAY)

	def release(self):
		if self._buffer is not None:
			glBindBuffer(GL_ARRAY_BUFFER, self._buffer)
			glBufferData(GL_ARRAY_BUFFER, None, GL_STATIC_DRAW)
			glBindBuffer(GL_ARRAY_BUFFER, 0)
			glDeleteBuffers(1, [self._buffer])
			self._buffer = None
		self._vertexArray = None
		self._normalArray = None

	def __del__(self):
		if self._buffer is not None and bool(glDeleteBuffers):
			print "VBO was not properly released!"

def glDrawStringCenter(s):
	glRasterPos2f(0, 0)
	glBitmap(0,0,0,0, -glGetStringSize(s)[0]/2, 0, None)
	for c in s:
		glutBitmapCharacter(OpenGL.GLUT.GLUT_BITMAP_HELVETICA_18, ord(c))

def glGetStringSize(s):
	width = 0
	for c in s:
		width += glutBitmapWidth(OpenGL.GLUT.GLUT_BITMAP_HELVETICA_18, ord(c))
	height = 18
	return width, height

def glDrawStringLeft(s):
	glRasterPos2f(0, 0)
	n = 1
	for c in s:
		if c == '\n':
			glPushMatrix()
			glTranslate(0, 18 * n, 0)
			n += 1
			glRasterPos2f(0, 0)
			glPopMatrix()
		else:
			glutBitmapCharacter(OpenGL.GLUT.GLUT_BITMAP_HELVETICA_18, ord(c))

def glDrawStringRight(s):
	glRasterPos2f(0, 0)
	glBitmap(0,0,0,0, -glGetStringSize(s)[0], 0, None)
	for c in s:
		glutBitmapCharacter(OpenGL.GLUT.GLUT_BITMAP_HELVETICA_18, ord(c))

def glDrawQuad(x, y, w, h):
	glPushMatrix()
	glTranslatef(x, y, 0)
	glDisable(GL_TEXTURE_2D)
	glBegin(GL_QUADS)
	glVertex2f(w, 0)
	glVertex2f(0, 0)
	glVertex2f(0, h)
	glVertex2f(w, h)
	glEnd()
	glPopMatrix()

def glDrawTexturedQuad(x, y, w, h, texID, mirror = 0):
	tx = float(texID % 4) / 4
	ty = float(int(texID / 4)) / 8
	tsx = 0.25
	tsy = 0.125
	if mirror & 1:
		tx += tsx
		tsx = -tsx
	if mirror & 2:
		ty += tsy
		tsy = -tsy
	glPushMatrix()
	glTranslatef(x, y, 0)
	glEnable(GL_TEXTURE_2D)
	glBegin(GL_QUADS)
	glTexCoord2f(tx+tsx, ty)
	glVertex2f(w, 0)
	glTexCoord2f(tx, ty)
	glVertex2f(0, 0)
	glTexCoord2f(tx, ty+tsy)
	glVertex2f(0, h)
	glTexCoord2f(tx+tsx, ty+tsy)
	glVertex2f(w, h)
	glEnd()
	glPopMatrix()

def glDrawStretchedQuad(x, y, w, h, cornerSize, texID):
	tx0 = float(texID % 4) / 4
	ty0 = float(int(texID / 4)) / 8
	tx1 = tx0 + 0.25 / 2.0
	ty1 = ty0 + 0.125 / 2.0
	tx2 = tx0 + 0.25
	ty2 = ty0 + 0.125

	glPushMatrix()
	glTranslatef(x, y, 0)
	glEnable(GL_TEXTURE_2D)
	glBegin(GL_QUADS)
	#TopLeft
	glTexCoord2f(tx1, ty0)
	glVertex2f( cornerSize, 0)
	glTexCoord2f(tx0, ty0)
	glVertex2f( 0, 0)
	glTexCoord2f(tx0, ty1)
	glVertex2f( 0, cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, cornerSize)
	#TopRight
	glTexCoord2f(tx2, ty0)
	glVertex2f( w, 0)
	glTexCoord2f(tx1, ty0)
	glVertex2f( w - cornerSize, 0)
	glTexCoord2f(tx1, ty1)
	glVertex2f( w - cornerSize, cornerSize)
	glTexCoord2f(tx2, ty1)
	glVertex2f( w, cornerSize)
	#BottomLeft
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, h - cornerSize)
	glTexCoord2f(tx0, ty1)
	glVertex2f( 0, h - cornerSize)
	glTexCoord2f(tx0, ty2)
	glVertex2f( 0, h)
	glTexCoord2f(tx1, ty2)
	glVertex2f( cornerSize, h)
	#BottomRight
	glTexCoord2f(tx2, ty1)
	glVertex2f( w, h - cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( w - cornerSize, h - cornerSize)
	glTexCoord2f(tx1, ty2)
	glVertex2f( w - cornerSize, h)
	glTexCoord2f(tx2, ty2)
	glVertex2f( w, h)

	#Center
	glTexCoord2f(tx1, ty1)
	glVertex2f( w-cornerSize, cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, h-cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( w-cornerSize, h-cornerSize)

	#Right
	glTexCoord2f(tx2, ty1)
	glVertex2f( w, cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( w-cornerSize, cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( w-cornerSize, h-cornerSize)
	glTexCoord2f(tx2, ty1)
	glVertex2f( w, h-cornerSize)

	#Left
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, cornerSize)
	glTexCoord2f(tx0, ty1)
	glVertex2f( 0, cornerSize)
	glTexCoord2f(tx0, ty1)
	glVertex2f( 0, h-cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, h-cornerSize)

	#Top
	glTexCoord2f(tx1, ty0)
	glVertex2f( w-cornerSize, 0)
	glTexCoord2f(tx1, ty0)
	glVertex2f( cornerSize, 0)
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( w-cornerSize, cornerSize)

	#Bottom
	glTexCoord2f(tx1, ty1)
	glVertex2f( w-cornerSize, h-cornerSize)
	glTexCoord2f(tx1, ty1)
	glVertex2f( cornerSize, h-cornerSize)
	glTexCoord2f(tx1, ty2)
	glVertex2f( cornerSize, h)
	glTexCoord2f(tx1, ty2)
	glVertex2f( w-cornerSize, h)

	glEnd()
	glDisable(GL_TEXTURE_2D)
	glPopMatrix()

def unproject(winx, winy, winz, modelMatrix, projMatrix, viewport):
	npModelMatrix = numpy.matrix(numpy.array(modelMatrix, numpy.float64).reshape((4,4)))
	npProjMatrix = numpy.matrix(numpy.array(projMatrix, numpy.float64).reshape((4,4)))
	finalMatrix = npModelMatrix * npProjMatrix
	finalMatrix = numpy.linalg.inv(finalMatrix)

	viewport = map(float, viewport)
	vector = numpy.array([(winx - viewport[0]) / viewport[2] * 2.0 - 1.0, (winy - viewport[1]) / viewport[3] * 2.0 - 1.0, winz * 2.0 - 1.0, 1]).reshape((1,4))
	vector = (numpy.matrix(vector) * finalMatrix).getA().flatten()
	ret = list(vector)[0:3] / vector[3]
	return ret

def convert3x3MatrixTo4x4(matrix):
	return list(matrix.getA()[0]) + [0] + list(matrix.getA()[1]) + [0] + list(matrix.getA()[2]) + [0, 0,0,0,1]

def loadGLTexture(filename):
	tex = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, tex)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	img = wx.ImageFromBitmap(wx.Bitmap(getPathForImage(filename)))
	rgbData = img.GetData()
	alphaData = img.GetAlphaData()
	if alphaData is not None:
		data = ''
		for i in xrange(0, len(alphaData)):
			data += rgbData[i*3:i*3+3] + alphaData[i]
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.GetWidth(), img.GetHeight(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
	else:
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.GetWidth(), img.GetHeight(), 0, GL_RGB, GL_UNSIGNED_BYTE, rgbData)
	return tex

def ResetMatrixRotationAndScale():
	matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
	noZ = False
	if matrix[3][2] > 0:
		return False
	scale2D = matrix[0][0]
	matrix[0][0] = 1.0
	matrix[1][0] = 0.0
	matrix[2][0] = 0.0
	matrix[0][1] = 0.0
	matrix[1][1] = 1.0
	matrix[2][1] = 0.0
	matrix[0][2] = 0.0
	matrix[1][2] = 0.0
	matrix[2][2] = 1.0

	if matrix[3][2] != 0.0:
		matrix[3][0] = matrix[3][0] / (-matrix[3][2] / 100)
		matrix[3][1] = matrix[3][1] / (-matrix[3][2] / 100)
		matrix[3][2] = -100
	else:
		matrix[0][0] = scale2D
		matrix[1][1] = scale2D
		matrix[2][2] = scale2D
		matrix[3][2] = -100
		noZ = True

	glLoadMatrixf(matrix)
	return noZ


def DrawBox(vMin, vMax):
	glBegin(GL_LINE_LOOP)
	glVertex3f(vMin[0], vMin[1], vMin[2])
	glVertex3f(vMax[0], vMin[1], vMin[2])
	glVertex3f(vMax[0], vMax[1], vMin[2])
	glVertex3f(vMin[0], vMax[1], vMin[2])
	glEnd()

	glBegin(GL_LINE_LOOP)
	glVertex3f(vMin[0], vMin[1], vMax[2])
	glVertex3f(vMax[0], vMin[1], vMax[2])
	glVertex3f(vMax[0], vMax[1], vMax[2])
	glVertex3f(vMin[0], vMax[1], vMax[2])
	glEnd()
	glBegin(GL_LINES)
	glVertex3f(vMin[0], vMin[1], vMin[2])
	glVertex3f(vMin[0], vMin[1], vMax[2])
	glVertex3f(vMax[0], vMin[1], vMin[2])
	glVertex3f(vMax[0], vMin[1], vMax[2])
	glVertex3f(vMax[0], vMax[1], vMin[2])
	glVertex3f(vMax[0], vMax[1], vMax[2])
	glVertex3f(vMin[0], vMax[1], vMin[2])
	glVertex3f(vMin[0], vMax[1], vMax[2])
	glEnd()


def DrawMeshOutline(mesh):
	glEnable(GL_CULL_FACE)
	glEnableClientState(GL_VERTEX_ARRAY);
	glVertexPointer(3, GL_FLOAT, 0, mesh.vertexes)

	glCullFace(GL_FRONT)
	glLineWidth(3)
	glPolygonMode(GL_BACK, GL_LINE)
	glDrawArrays(GL_TRIANGLES, 0, mesh.vertexCount)
	glPolygonMode(GL_BACK, GL_FILL)
	glCullFace(GL_BACK)

	glDisableClientState(GL_VERTEX_ARRAY)


def DrawMesh(mesh, insideOut = False):
	glEnable(GL_CULL_FACE)
	glEnableClientState(GL_VERTEX_ARRAY)
	glEnableClientState(GL_NORMAL_ARRAY)
	for m in mesh._meshList:
		glVertexPointer(3, GL_FLOAT, 0, m.vertexes)
		if insideOut:
			glNormalPointer(GL_FLOAT, 0, m.invNormal)
		else:
			glNormalPointer(GL_FLOAT, 0, m.normal)

		#Odd, drawing in batchs is a LOT faster then drawing it all at once.
		batchSize = 999    #Warning, batchSize needs to be dividable by 3
		extraStartPos = int(m.vertexCount / batchSize) * batchSize
		extraCount = m.vertexCount - extraStartPos

		glCullFace(GL_BACK)
		for i in xrange(0, int(m.vertexCount / batchSize)):
			glDrawArrays(GL_TRIANGLES, i * batchSize, batchSize)
		glDrawArrays(GL_TRIANGLES, extraStartPos, extraCount)

		glCullFace(GL_FRONT)
		if insideOut:
			glNormalPointer(GL_FLOAT, 0, m.normal)
		else:
			glNormalPointer(GL_FLOAT, 0, m.invNormal)
		for i in xrange(0, int(m.vertexCount / batchSize)):
			glDrawArrays(GL_TRIANGLES, i * batchSize, batchSize)
		extraStartPos = int(m.vertexCount / batchSize) * batchSize
		extraCount = m.vertexCount - extraStartPos
		glDrawArrays(GL_TRIANGLES, extraStartPos, extraCount)
		glCullFace(GL_BACK)

	glDisableClientState(GL_VERTEX_ARRAY)
	glDisableClientState(GL_NORMAL_ARRAY)


def DrawMeshSteep(mesh, matrix, angle):
	cosAngle = math.sin(angle / 180.0 * math.pi)
	glDisable(GL_LIGHTING)
	glDepthFunc(GL_EQUAL)
	normals = (numpy.matrix(mesh.normal, copy = False) * matrix).getA()
	for i in xrange(0, int(mesh.vertexCount), 3):
		if normals[i][2] < -0.999999:
			if mesh.vertexes[i + 0][2] > 0.01:
				glColor3f(0.5, 0, 0)
				glBegin(GL_TRIANGLES)
				glVertex3f(mesh.vertexes[i + 0][0], mesh.vertexes[i + 0][1], mesh.vertexes[i + 0][2])
				glVertex3f(mesh.vertexes[i + 1][0], mesh.vertexes[i + 1][1], mesh.vertexes[i + 1][2])
				glVertex3f(mesh.vertexes[i + 2][0], mesh.vertexes[i + 2][1], mesh.vertexes[i + 2][2])
				glEnd()
		elif normals[i][2] < -cosAngle:
			glColor3f(-normals[i][2], 0, 0)
			glBegin(GL_TRIANGLES)
			glVertex3f(mesh.vertexes[i + 0][0], mesh.vertexes[i + 0][1], mesh.vertexes[i + 0][2])
			glVertex3f(mesh.vertexes[i + 1][0], mesh.vertexes[i + 1][1], mesh.vertexes[i + 1][2])
			glVertex3f(mesh.vertexes[i + 2][0], mesh.vertexes[i + 2][1], mesh.vertexes[i + 2][2])
			glEnd()
		elif normals[i][2] > 0.999999:
			if mesh.vertexes[i + 0][2] > 0.01:
				glColor3f(0.5, 0, 0)
				glBegin(GL_TRIANGLES)
				glVertex3f(mesh.vertexes[i + 0][0], mesh.vertexes[i + 0][1], mesh.vertexes[i + 0][2])
				glVertex3f(mesh.vertexes[i + 2][0], mesh.vertexes[i + 2][1], mesh.vertexes[i + 2][2])
				glVertex3f(mesh.vertexes[i + 1][0], mesh.vertexes[i + 1][1], mesh.vertexes[i + 1][2])
				glEnd()
		elif normals[i][2] > cosAngle:
			glColor3f(normals[i][2], 0, 0)
			glBegin(GL_TRIANGLES)
			glVertex3f(mesh.vertexes[i + 0][0], mesh.vertexes[i + 0][1], mesh.vertexes[i + 0][2])
			glVertex3f(mesh.vertexes[i + 2][0], mesh.vertexes[i + 2][1], mesh.vertexes[i + 2][2])
			glVertex3f(mesh.vertexes[i + 1][0], mesh.vertexes[i + 1][1], mesh.vertexes[i + 1][2])
			glEnd()
	glDepthFunc(GL_LESS)

def DrawGCodeLayer(layer, drawQuick = True):
	filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
	filamentArea = math.pi * filamentRadius * filamentRadius
	lineWidth = profile.getProfileSettingFloat('nozzle_size') / 2 / 10

	fillCycle = 0
	fillColorCycle = [[0.5, 0.5, 0.0, 1], [0.0, 0.5, 0.5, 1], [0.5, 0.0, 0.5, 1]]
	moveColor = [0, 0, 1, 0.5]
	retractColor = [1, 0, 0.5, 0.5]
	supportColor = [0, 1, 1, 1]
	extrudeColor = [[1, 0, 0, 1], [0, 1, 1, 1], [1, 1, 0, 1], [1, 0, 1, 1]]
	innerWallColor = [0, 1, 0, 1]
	skirtColor = [0, 0.5, 0.5, 1]
	prevPathWasRetract = False

	glDisable(GL_CULL_FACE)
	for path in layer:
		if path.type == 'move':
			if prevPathWasRetract:
				c = retractColor
			else:
				c = moveColor
			if drawQuick:
				continue
		zOffset = 0.01
		if path.type == 'extrude':
			if path.pathType == 'FILL':
				c = fillColorCycle[fillCycle]
				fillCycle = (fillCycle + 1) % len(fillColorCycle)
			elif path.pathType == 'WALL-INNER':
				c = innerWallColor
				zOffset = 0.02
			elif path.pathType == 'SUPPORT':
				c = supportColor
			elif path.pathType == 'SKIRT':
				c = skirtColor
			else:
				c = extrudeColor[path.extruder]
		if path.type == 'retract':
			c = retractColor
		if path.type == 'extrude' and not drawQuick:
			drawLength = 0.0
			prevNormal = None
			for i in xrange(0, len(path.points) - 1):
				v0 = path.points[i]
				v1 = path.points[i + 1]

				# Calculate line width from ePerDistance (needs layer thickness and filament diameter)
				dist = (v0 - v1).vsize()
				if dist > 0 and path.layerThickness > 0:
					extrusionMMperDist = (v1.e - v0.e) / dist
					lineWidth = extrusionMMperDist * filamentArea / path.layerThickness / 2 * v1.extrudeAmountMultiply

				drawLength += (v0 - v1).vsize()
				normal = (v0 - v1).cross(util3d.Vector3(0, 0, 1))
				normal.normalize()

				vv2 = v0 + normal * lineWidth
				vv3 = v1 + normal * lineWidth
				vv0 = v0 - normal * lineWidth
				vv1 = v1 - normal * lineWidth

				glBegin(GL_QUADS)
				glColor4fv(c)
				glVertex3f(vv0.x, vv0.y, vv0.z - zOffset)
				glVertex3f(vv1.x, vv1.y, vv1.z - zOffset)
				glVertex3f(vv3.x, vv3.y, vv3.z - zOffset)
				glVertex3f(vv2.x, vv2.y, vv2.z - zOffset)
				glEnd()
				if prevNormal is not None:
					n = (normal + prevNormal)
					n.normalize()
					vv4 = v0 + n * lineWidth
					vv5 = v0 - n * lineWidth
					glBegin(GL_QUADS)
					glColor4fv(c)
					glVertex3f(vv2.x, vv2.y, vv2.z - zOffset)
					glVertex3f(vv4.x, vv4.y, vv4.z - zOffset)
					glVertex3f(prevVv3.x, prevVv3.y, prevVv3.z - zOffset)
					glVertex3f(v0.x, v0.y, v0.z - zOffset)

					glVertex3f(vv0.x, vv0.y, vv0.z - zOffset)
					glVertex3f(vv5.x, vv5.y, vv5.z - zOffset)
					glVertex3f(prevVv1.x, prevVv1.y, prevVv1.z - zOffset)
					glVertex3f(v0.x, v0.y, v0.z - zOffset)
					glEnd()

				prevNormal = normal
				prevVv1 = vv1
				prevVv3 = vv3
		else:
			glColor4fv(c)
			glBegin(GL_TRIANGLES)
			for v in path.points:
				glVertex3f(v[0], v[1], v[2])
			glEnd()

		if not path.type == 'move':
			prevPathWasRetract = False
		#if path.type == 'retract' and path.points[0].almostEqual(path.points[-1]):
		#	prevPathWasRetract = True
	glEnable(GL_CULL_FACE)
