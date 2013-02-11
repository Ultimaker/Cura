from __future__ import absolute_import
from __future__ import division

import wx
from wx import glcanvas
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *

from Cura.gui.util import opengl

class glGuiControl(object):
	def __init__(self, parent, pos):
		self._parent = parent
		self._base = parent._base
		self._pos = pos
		self._size = (0,0, 1, 1)
		self._parent.add(self)

	def setSize(self, x, y, w, h):
		self._size = (x, y, w, h)

	def getSize(self):
		return self._size

	def getMinSize(self):
		return 1, 1

	def updateLayout(self):
		pass

	def focusNext(self):
		for n in xrange(self._parent._glGuiControlList.index(self) + 1, len(self._parent._glGuiControlList)):
			if self._parent._glGuiControlList[n].setFocus():
				return
		for n in xrange(0, self._parent._glGuiControlList.index(self)):
			if self._parent._glGuiControlList[n].setFocus():
				return

	def focusPrevious(self):
		for n in xrange(self._parent._glGuiControlList.index(self) -1, -1, -1):
			if self._parent._glGuiControlList[n].setFocus():
				return
		for n in xrange(len(self._parent._glGuiControlList) - 1, self._parent._glGuiControlList.index(self), -1):
			if self._parent._glGuiControlList[n].setFocus():
				return

	def setFocus(self):
		return False

class glGuiContainer(glGuiControl):
	def __init__(self, parent, pos):
		self._glGuiControlList = []
		glGuiLayoutButtons(self)
		super(glGuiContainer, self).__init__(parent, pos)

	def add(self, ctrl):
		self._glGuiControlList.append(ctrl)
		self.updateLayout()

	def OnMouseDown(self, x, y):
		for ctrl in self._glGuiControlList:
			if ctrl.OnMouseDown(x, y):
				return True
		return False

	def OnMouseMotion(self, x, y):
		handled = False
		for ctrl in self._glGuiControlList:
			if ctrl.OnMouseMotion(x, y):
				handled = True
		return handled

	def draw(self):
		for ctrl in self._glGuiControlList:
			ctrl.draw()

	def updateLayout(self):
		self._layout.update()
		for ctrl in self._glGuiControlList:
			ctrl.updateLayout()

class glGuiPanel(glcanvas.GLCanvas):
	def __init__(self, parent):
		attribList = (glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 24, glcanvas.WX_GL_STENCIL_SIZE, 8)
		glcanvas.GLCanvas.__init__(self, parent, style=wx.WANTS_CHARS, attribList = attribList)
		self._base = self
		self._focus = None
		self._container = None
		self._container = glGuiContainer(self, (0,0))

		self._context = glcanvas.GLContext(self)
		self._glButtonsTexture = None
		self._buttonSize = 64

		wx.EVT_PAINT(self, self._OnGuiPaint)
		wx.EVT_SIZE(self, self._OnSize)
		wx.EVT_ERASE_BACKGROUND(self, self._OnEraseBackground)
		wx.EVT_LEFT_DOWN(self, self._OnGuiMouseLeftDown)
		wx.EVT_MOTION(self, self._OnGuiMouseMotion)
		wx.EVT_CHAR(self, self.OnKeyChar)
		wx.EVT_KILL_FOCUS(self, self.OnFocusLost)

	def OnKeyChar(self, e):
		if self._focus is not None:
			self._focus.OnKeyChar(e.GetKeyCode())
			self.Refresh()

	def OnFocusLost(self, e):
		self._focus = None
		self.Refresh()

	def _OnGuiMouseLeftDown(self,e):
		self.SetFocus()
		if self._container.OnMouseDown(e.GetX(), e.GetY()):
			self.Refresh()
			return
		self.OnMouseLeftDown(e)

	def _OnGuiMouseMotion(self,e):
		self.Refresh()
		if not self._container.OnMouseMotion(e.GetX(), e.GetY()):
			self.OnMouseMotion(e)

	def _OnGuiPaint(self, e):
		h = self.GetSize().GetHeight()
		w = self.GetSize().GetWidth()
		oldButtonSize = self._buttonSize
		if h / 3 > w / 4:
			w = h * 4 / 3
		if w < 64 * 10:
			self._buttonSize = 48
		elif w < 64 * 15:
			self._buttonSize = 64
		elif w < 64 * 20:
			self._buttonSize = 80
		else:
			self._buttonSize = 96
		if self._buttonSize != oldButtonSize:
			self._container.updateLayout()

		dc = wx.PaintDC(self)
		self.SetCurrent(self._context)
		self.OnPaint(e)
		self._drawGui()
		glFlush()
		self.SwapBuffers()

	def _drawGui(self):
		if self._glButtonsTexture is None:
			self._glButtonsTexture = opengl.loadGLTexture('glButtons.png')

		glDisable(GL_DEPTH_TEST)
		glEnable(GL_BLEND)
		glDisable(GL_LIGHTING)
		glColor4ub(255,255,255,255)

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		size = self.GetSize()
		glOrtho(0, size.GetWidth()-1, size.GetHeight()-1, 0, -1000.0, 1000.0)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

		self._container.draw()

	def _OnEraseBackground(self,event):
		#Workaround for windows background redraw flicker.
		pass

	def _OnSize(self,e):
		self._container.setSize(0, 0, self.GetSize().GetWidth(), self.GetSize().GetHeight())
		self._container.updateLayout()
		self.Refresh()

	def OnMouseLeftDown(self,e):
		pass
	def OnMouseMotion(self, e):
		pass
	def OnPaint(self, e):
		pass

	def add(self, ctrl):
		if self._container is not None:
			self._container.add(ctrl)

class glGuiLayoutButtons(object):
	def __init__(self, parent):
		self._parent = parent
		self._parent._layout = self

	def update(self):
		bs = self._parent._base._buttonSize
		x0, y0, w, h = self._parent.getSize()
		gridSize = bs * 1.3
		for ctrl in self._parent._glGuiControlList:
			pos = ctrl._pos
			if pos[0] < 0:
				x = w + pos[0] * gridSize - bs * 0.2
			else:
				x = pos[0] * gridSize + bs * 0.2
			if pos[1] < 0:
				y = h + pos[1] * gridSize - bs * 0.2
			else:
				y = pos[1] * gridSize + bs * 0.2
			ctrl.setSize(x, y, gridSize, gridSize)

	def getLayoutSize(self):
		_, _, w, h = self._parent.getSize()
		return w, h

class glGuiLayoutGrid(object):
	def __init__(self, parent):
		self._parent = parent
		self._parent._layout = self
		self._size = 0,0

	def update(self):
		borderSize = self._parent._base._buttonSize * 0.2
		x0, y0, w, h = self._parent.getSize()
		x0 += borderSize
		y0 += borderSize
		widths = {}
		heights = {}
		for ctrl in self._parent._glGuiControlList:
			x, y = ctrl._pos
			w, h = ctrl.getMinSize()
			if not x in widths:
				widths[x] = w
			else:
				widths[x] = max(widths[x], w)
			if not y in heights:
				heights[y] = h
			else:
				heights[y] = max(heights[y], h)
		for ctrl in self._parent._glGuiControlList:
			x, y = ctrl._pos
			x1 = x0
			y1 = y0
			for n in xrange(0, x):
				if not n in widths:
					widths[n] = 3
				x1 += widths[n]
			for n in xrange(0, y):
				if not n in heights:
					heights[n] = 3
				y1 += heights[n]
			ctrl.setSize(x1, y1, widths[x], heights[y])
		self._size = sum(widths.values()) + borderSize * 2, sum(heights.values()) + borderSize * 2

	def getLayoutSize(self):
		return self._size

class glButton(glGuiControl):
	def __init__(self, parent, imageID, tooltip, pos, callback):
		super(glButton, self).__init__(parent, pos)
		self._tooltip = tooltip
		self._parent = parent
		self._imageID = imageID
		self._callback = callback
		self._selected = False
		self._focus = False
		self._hidden = False
		self._disabled = False

	def setSelected(self, value):
		self._selected = value

	def setHidden(self, value):
		self._hidden = value

	def setDisabled(self, value):
		self._disabled = value

	def getSelected(self):
		return self._selected

	def getMinSize(self):
		return self._base._buttonSize, self._base._buttonSize

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0 + w / 2, y0 + h / 2

	def draw(self):
		if self._hidden:
			return

		cx = (self._imageID % 4) / 4
		cy = int(self._imageID / 4) / 4
		bs = self._base._buttonSize
		pos = self._getPixelPos()

		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
		glEnable(GL_TEXTURE_2D)
		scale = 0.8
		if self._selected:
			scale = 1.0
		elif self._focus:
			scale = 0.9
		glScalef(bs * scale, bs * scale, bs * scale)
		if self._disabled:
			glColor4ub(128,128,128,128)
		else:
			glColor4ub(255,255,255,255)
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
		if self._focus:
			glColor4ub(0,0,0,255)
			glTranslatef(0, -0.55, 0)
			opengl.glDrawStringCenter(self._tooltip)
		glPopMatrix()

	def _checkHit(self, x, y):
		if self._hidden or self._disabled:
			return False
		bs = self.getMinSize()[0]
		pos = self._getPixelPos()
		return -bs * 0.5 <= x - pos[0] <= bs * 0.5 and -bs * 0.5 <= y - pos[1] <= bs * 0.5

	def OnMouseMotion(self, x, y):
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y):
		if self._checkHit(x, y):
			self._callback()
			return True
		return False

class glRadioButton(glButton):
	def __init__(self, parent, imageID, tooltip, pos, group, callback):
		super(glRadioButton, self).__init__(parent, imageID, tooltip, pos, self._onRadioSelect)
		self._group = group
		self._radioCallback = callback
		self._group.append(self)

	def setSelected(self, value):
		self._selected = value

	def _onRadioSelect(self):
		for ctrl in self._group:
			if ctrl != self:
				ctrl.setSelected(False)
		if self.getSelected():
			self.setSelected(False)
		else:
			self.setSelected(True)
		self._radioCallback()

class glFrame(glGuiContainer):
	def __init__(self, parent, pos):
		super(glFrame, self).__init__(parent, pos)
		self._selected = False
		self._focus = False
		self._hidden = False

	def setSelected(self, value):
		self._selected = value

	def setHidden(self, value):
		self._hidden = value

	def getSelected(self):
		return self._selected

	def getMinSize(self):
		return self._base._buttonSize, self._base._buttonSize

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0, y0

	def draw(self):
		if self._hidden:
			return

		bs = self._parent._buttonSize
		pos = self._getPixelPos()

		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glBindTexture(GL_TEXTURE_2D, self._parent._glButtonsTexture)
		glEnable(GL_TEXTURE_2D)

		size = self._layout.getLayoutSize()
		glColor4ub(255,255,255,128)
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f( size[0], 0)
		glTexCoord2f(0, 0)
		glVertex2f( 0, 0)
		glTexCoord2f(0, 1)
		glVertex2f( 0, size[1])
		glTexCoord2f(1, 1)
		glVertex2f( size[0], size[1])
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()
		#Draw the controls on the frame
		super(glFrame, self).draw()

	def _checkHit(self, x, y):
		if self._hidden:
			return False
		pos = self._getPixelPos()
		w, h = self._layout.getLayoutSize()
		return 0 <= x - pos[0] <= w and 0 <= y - pos[1] <= h

	def OnMouseMotion(self, x, y):
		super(glFrame, self).OnMouseMotion(x, y)
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y):
		if self._checkHit(x, y):
			super(glFrame, self).OnMouseDown(x, y)
			return True
		return False

class glLabel(glGuiControl):
	def __init__(self, parent, label, pos):
		self._label = label
		super(glLabel, self).__init__(parent, pos)

	def getMinSize(self):
		w, h = opengl.glGetStringSize(self._label)
		return w + 10, h + 4

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0, y0

	def draw(self):
		x, y, w, h = self.getSize()

		glPushMatrix()
		glTranslatef(x, y, 0)

		glColor4ub(255,255,255,128)
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f( w, 0)
		glTexCoord2f(0, 0)
		glVertex2f( 0, 0)
		glTexCoord2f(0, 1)
		glVertex2f( 0, h)
		glTexCoord2f(1, 1)
		glVertex2f( w, h)
		glEnd()

		glTranslate(5, h - 5, 0)
		glColor4ub(0,0,0,255)
		opengl.glDrawStringLeft(self._label)
		glPopMatrix()

	def _checkHit(self, x, y):
		return False

	def OnMouseMotion(self, x, y):
		return False

	def OnMouseDown(self, x, y):
		return False

class glNumberCtrl(glGuiControl):
	def __init__(self, parent, value, pos, callback):
		self._callback = callback
		self._value = str(value)
		self._selectPos = 0
		self._maxLen = 6
		self._inCallback = False
		super(glNumberCtrl, self).__init__(parent, pos)

	def setValue(self, value):
		if self._inCallback:
			return
		self._value = str(value)

	def getMinSize(self):
		w, h = opengl.glGetStringSize("VALUES")
		return w + 10, h + 4

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0, y0

	def draw(self):
		x, y, w, h = self.getSize()

		glPushMatrix()
		glTranslatef(x, y, 0)

		if self._base._focus == self:
			glColor4ub(255,255,255,255)
		else:
			glColor4ub(255,255,255,192)
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f( w, 0)
		glTexCoord2f(0, 0)
		glVertex2f( 0, 0)
		glTexCoord2f(0, 1)
		glVertex2f( 0, h)
		glTexCoord2f(1, 1)
		glVertex2f( w, h)
		glEnd()

		glTranslate(5, h - 5, 0)
		glColor4ub(0,0,0,255)
		opengl.glDrawStringLeft(self._value)
		if self._base._focus == self:
			glTranslate(opengl.glGetStringSize(self._value[0:self._selectPos])[0] - 2, -1, 0)
			opengl.glDrawStringLeft('|')
		glPopMatrix()

	def _checkHit(self, x, y):
		x1, y1, w, h = self.getSize()
		return 0 <= x - x1 <= w and 0 <= y - y1 <= h

	def OnMouseMotion(self, x, y):
		return False

	def OnMouseDown(self, x, y):
		if self._checkHit(x, y):
			self.setFocus()
			return True
		return False

	def OnKeyChar(self, c):
		self._inCallback = True
		if c == wx.WXK_LEFT:
			self._selectPos -= 1
			self._selectPos = max(0, self._selectPos)
		if c == wx.WXK_RIGHT:
			self._selectPos += 1
			self._selectPos = min(self._selectPos, len(self._value))
		if c == wx.WXK_UP:
			try:
				value = float(self._value)
			except:
				pass
			else:
				value += 0.1
				self._value = str(value)
				self._callback(self._value)
		if c == wx.WXK_DOWN:
			try:
				value = float(self._value)
			except:
				pass
			else:
				value -= 0.1
				if value > 0:
					self._value = str(value)
					self._callback(self._value)
		if c == wx.WXK_BACK and self._selectPos > 0:
			self._value = self._value[0:self._selectPos - 1] + self._value[self._selectPos:]
			self._selectPos -= 1
			self._callback(self._value)
		if c == wx.WXK_DELETE:
			self._value = self._value[0:self._selectPos] + self._value[self._selectPos + 1:]
			self._callback(self._value)
		if c == wx.WXK_TAB:
			if wx.GetKeyState(wx.WXK_SHIFT):
				self.focusPrevious()
			else:
				self.focusNext()
		if (ord('0') <= c <= ord('9') or c == ord('.')) and len(self._value) < self._maxLen:
			self._value = self._value[0:self._selectPos] + chr(c) + self._value[self._selectPos:]
			self._selectPos += 1
			self._callback(self._value)
		self._inCallback = False

	def setFocus(self):
		self._base._focus = self
		self._selectPos = len(self._value)
		return True

class glCheckbox(glGuiControl):
	def __init__(self, parent, value, pos, callback):
		self._callback = callback
		self._value = value
		self._selectPos = 0
		self._maxLen = 6
		self._inCallback = False
		super(glCheckbox, self).__init__(parent, pos)

	def setValue(self, value):
		if self._inCallback:
			return
		self._value = str(value)

	def getValue(self):
		return self._value

	def getMinSize(self):
		return 20, 20

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		return x0, y0

	def draw(self):
		x, y, w, h = self.getSize()

		glPushMatrix()
		glTranslatef(x, y, 0)

		if self._value:
			glColor4ub(0,255,0,255)
		else:
			glColor4ub(255,0,0,255)
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f( w, 0)
		glTexCoord2f(0, 0)
		glVertex2f( 0, 0)
		glTexCoord2f(0, 1)
		glVertex2f( 0, h)
		glTexCoord2f(1, 1)
		glVertex2f( w, h)
		glEnd()

		glPopMatrix()

	def _checkHit(self, x, y):
		x1, y1, w, h = self.getSize()
		return 0 <= x - x1 <= w and 0 <= y - y1 <= h

	def OnMouseMotion(self, x, y):
		return False

	def OnMouseDown(self, x, y):
		if self._checkHit(x, y):
			self._value = not self._value
			return True
		return False
