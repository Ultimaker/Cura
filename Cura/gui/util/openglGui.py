from __future__ import absolute_import
from __future__ import division

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *

from Cura.gui.util import opengl

glButtonsTexture = None

class glButton(object):
	def __init__(self, parent, imageID, x, y, callback):
		self._parent = parent
		self._imageID = imageID
		self._x = x
		self._y = y
		self._callback = callback
		self._parent.glButtonList.append(self)
		self._selected = False
		self._focus = False
		self._hidden = False

	def setSelected(self, value):
		self._selected = value

	def setHidden(self, value):
		self._hidden = value

	def getSelected(self):
		return self._selected

	def draw(self):
		global glButtonsTexture
		if self._hidden:
			return
		if glButtonsTexture is None:
			glButtonsTexture = opengl.loadGLTexture('glButtons.png')

		cx = (self._imageID % 4) / 4
		cy = int(self._imageID / 4) / 4
		bs = self._parent.buttonSize

		glPushMatrix()
		glTranslatef(self._x * bs * 1.3 + bs * 0.8, self._y * bs * 1.3 + bs * 0.8, 0)
		glBindTexture(GL_TEXTURE_2D, glButtonsTexture)
		glEnable(GL_TEXTURE_2D)
		scale = 0.8
		if self._selected:
			scale = 1.0
		elif self._focus:
			scale = 0.9
		glScalef(bs * scale, bs * scale, bs * scale)
		glBegin(GL_QUADS)
		glTexCoord2f(cx+0.25, cy)
		glVertex2f( 0.5,-0.5)
		glTexCoord2f(cx, cy)
		glVertex2f(-0.5,-0.5)
		glTexCoord2f(cx, cy+0.25)
		glVertex2f(-0.5, 0.5)
		glTexCoord2f(cx+0.25, cy+0.25)
		glVertex2f( 0.5, 0.5)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()

	def _checkHit(self, x, y):
		if self._hidden:
			return False
		bs = self._parent.buttonSize
		return -bs * 0.5 <= x - (self._x * bs * 1.3 + bs * 0.8) <= bs * 0.5 and -bs * 0.5 <= y - (self._y * bs * 1.3 + bs * 0.8) <= bs * 0.5

	def OnMouseMotion(self, x, y):
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y):
		if self._checkHit(x, y):
			self._callback()
