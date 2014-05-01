__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import math
import numpy
import wx
import time

from Cura.util.resources import getPathForImage

import OpenGL

OpenGL.ERROR_CHECKING = False
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.GL import shaders
glutInit() #Hack; required before glut can be called. Not required for all OS.

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
			# This is to ensure that this works on intel GPU's
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

class GLFakeShader(GLReferenceCounter):
	"""
	A Class that acts as an OpenGL shader, but in reality is not one. Used if shaders are not supported.
	"""
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
	"""
	Vertex buffer object. Used for faster rendering.
	"""
	def __init__(self, renderType, vertexArray, normalArray = None, indicesArray = None):
		super(GLVBO, self).__init__()
		# TODO: Add size check to see if normal and vertex arrays have same size.
		self._renderType = renderType
		if not bool(glGenBuffers): # Fallback if buffers are not supported.
			self._vertexArray = vertexArray
			self._normalArray = normalArray
			self._indicesArray = indicesArray
			self._size = len(vertexArray)
			self._buffers = None
			self._hasNormals = self._normalArray is not None
			self._hasIndices = self._indicesArray is not None
			if self._hasIndices:
				self._size = len(indicesArray)
		else:
			self._buffers = []
			self._size = len(vertexArray)
			self._hasNormals = normalArray is not None
			self._hasIndices = indicesArray is not None
			maxVertsPerBuffer = 30000
			if self._hasIndices:
				maxVertsPerBuffer = self._size
			if maxVertsPerBuffer > 0:
				bufferCount = ((self._size-1) / maxVertsPerBuffer) + 1
				for n in xrange(0, bufferCount):
					bufferInfo = {
						'buffer': glGenBuffers(1),
						'size': maxVertsPerBuffer
					}
					offset = n * maxVertsPerBuffer
					if n == bufferCount - 1:
						bufferInfo['size'] = ((self._size - 1) % maxVertsPerBuffer) + 1
					glBindBuffer(GL_ARRAY_BUFFER, bufferInfo['buffer'])
					if self._hasNormals:
						glBufferData(GL_ARRAY_BUFFER, numpy.concatenate((vertexArray[offset:offset+bufferInfo['size']], normalArray[offset:offset+bufferInfo['size']]), 1), GL_STATIC_DRAW)
					else:
						glBufferData(GL_ARRAY_BUFFER, vertexArray[offset:offset+bufferInfo['size']], GL_STATIC_DRAW)
					glBindBuffer(GL_ARRAY_BUFFER, 0)
					self._buffers.append(bufferInfo)
			if self._hasIndices:
				self._size = len(indicesArray)
				self._bufferIndices = glGenBuffers(1)
				glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._bufferIndices)
				glBufferData(GL_ELEMENT_ARRAY_BUFFER, numpy.array(indicesArray, numpy.uint32), GL_STATIC_DRAW)

	def render(self):
		glEnableClientState(GL_VERTEX_ARRAY)
		if self._buffers is None:
			glVertexPointer(3, GL_FLOAT, 0, self._vertexArray)
			if self._hasNormals:
				glEnableClientState(GL_NORMAL_ARRAY)
				glNormalPointer(GL_FLOAT, 0, self._normalArray)
			if self._hasIndices:
				glDrawElements(self._renderType, self._size, GL_UNSIGNED_INT, self._indicesArray)
			else:
				batchSize = 996	#Warning, batchSize needs to be dividable by 4 (quads), 3 (triangles) and 2 (lines). Current value is magic.
				extraStartPos = int(self._size / batchSize) * batchSize #leftovers.
				extraCount = self._size - extraStartPos
				for i in xrange(0, int(self._size / batchSize)):
					glDrawArrays(self._renderType, i * batchSize, batchSize)
				glDrawArrays(self._renderType, extraStartPos, extraCount)
		else:
			for info in self._buffers:
				glBindBuffer(GL_ARRAY_BUFFER, info['buffer'])
				if self._hasNormals:
					glEnableClientState(GL_NORMAL_ARRAY)
					glVertexPointer(3, GL_FLOAT, 2*3*4, c_void_p(0))
					glNormalPointer(GL_FLOAT, 2*3*4, c_void_p(3 * 4))
				else:
					glVertexPointer(3, GL_FLOAT, 3*4, c_void_p(0))
				if self._hasIndices:
					glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._bufferIndices)
					glDrawElements(self._renderType, self._size, GL_UNSIGNED_INT, c_void_p(0))
				else:
					glDrawArrays(self._renderType, 0, info['size'])

				glBindBuffer(GL_ARRAY_BUFFER, 0)
				if self._hasIndices:
					glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

		glDisableClientState(GL_VERTEX_ARRAY)
		if self._hasNormals:
			glDisableClientState(GL_NORMAL_ARRAY)

	def release(self):
		if self._buffers is not None:
			for info in self._buffers:
				glBindBuffer(GL_ARRAY_BUFFER, info['buffer'])
				glBufferData(GL_ARRAY_BUFFER, None, GL_STATIC_DRAW)
				glBindBuffer(GL_ARRAY_BUFFER, 0)
				glDeleteBuffers(1, [info['buffer']])
			self._buffers = None
			if self._hasIndices:
				glBindBuffer(GL_ARRAY_BUFFER, self._bufferIndices)
				glBufferData(GL_ARRAY_BUFFER, None, GL_STATIC_DRAW)
				glBindBuffer(GL_ARRAY_BUFFER, 0)
				glDeleteBuffers(1, [self._bufferIndices])
		self._vertexArray = None
		self._normalArray = None

	def __del__(self):
		if self._buffers is not None and bool(glDeleteBuffers):
			print "VBO was not properly released!"

def glDrawStringCenter(s):
	"""
	Draw string on current draw pointer position
	"""
	glRasterPos2f(0, 0)
	glBitmap(0,0,0,0, -glGetStringSize(s)[0]/2, 0, None)
	for c in s:
		glutBitmapCharacter(OpenGL.GLUT.GLUT_BITMAP_HELVETICA_18, ord(c))

def glGetStringSize(s):
	"""
	Get size in pixels of string
	"""
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
	"""
	Same as draw texured quad, but without stretching the corners. Useful for resizable windows.
	"""
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
	"""
	Projects window position to 3D space. (gluUnProject). Reimplentation as some drivers crash with the original.
	"""
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

def DrawBox(vMin, vMax):
	""" Draw wireframe box
	"""
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