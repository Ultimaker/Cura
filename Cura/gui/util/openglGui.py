from __future__ import absolute_import
from __future__ import division

import wx
import traceback
import sys
import os

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

	def hasFocus(self):
		return self._base._focus == self

	def OnMouseUp(self, x, y):
		pass

	def OnKeyChar(self, key):
		pass

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

	def OnMouseUp(self, x, y):
		for ctrl in self._glGuiControlList:
			if ctrl.OnMouseUp(x, y):
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
		self._shownError = False

		self._context = glcanvas.GLContext(self)
		self._glButtonsTexture = None
		self._glRobotTexture = None
		self._buttonSize = 64

		wx.EVT_PAINT(self, self._OnGuiPaint)
		wx.EVT_SIZE(self, self._OnSize)
		wx.EVT_ERASE_BACKGROUND(self, self._OnEraseBackground)
		wx.EVT_LEFT_DOWN(self, self._OnGuiMouseLeftDown)
		wx.EVT_LEFT_UP(self, self._OnGuiMouseLeftUp)
		wx.EVT_MOTION(self, self._OnGuiMouseMotion)
		wx.EVT_CHAR(self, self._OnGuiKeyChar)
		wx.EVT_KILL_FOCUS(self, self.OnFocusLost)

	def _OnGuiKeyChar(self, e):
		if self._focus is not None:
			self._focus.OnKeyChar(e.GetKeyCode())
			self.Refresh()
		else:
			self.OnKeyChar(e.GetKeyCode())

	def OnFocusLost(self, e):
		self._focus = None
		self.Refresh()

	def _OnGuiMouseLeftDown(self,e):
		self.SetFocus()
		if self._container.OnMouseDown(e.GetX(), e.GetY()):
			self.Refresh()
			return
		self.OnMouseLeftDown(e)
	def _OnGuiMouseLeftUp(self, e):
		if self._container.OnMouseUp(e.GetX(), e.GetY()):
			self.Refresh()
			return
		self.OnMouseLeftUp(e)

	def _OnGuiMouseMotion(self,e):
		self.Refresh()
		if not self._container.OnMouseMotion(e.GetX(), e.GetY()):
			self.OnMouseMotion(e)

	def _OnGuiPaint(self, e):
		h = self.GetSize().GetHeight()
		w = self.GetSize().GetWidth()
		oldButtonSize = self._buttonSize
		if h / 3 < w / 4:
			w = h * 4 / 3
		if w < 64 * 8:
			self._buttonSize = 32
		elif w < 64 * 10:
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
		try:
			self.SetCurrent(self._context)
			self.OnPaint(e)
			self._drawGui()
			glFlush()
			self.SwapBuffers()
		except:
			errStr = 'An error has occurred during the 3D view drawing.'
			tb = traceback.extract_tb(sys.exc_info()[2])
			errStr += "\n%s: '%s'" % (str(sys.exc_info()[0].__name__), str(sys.exc_info()[1]))
			for n in xrange(len(tb)-1, -1, -1):
				locationInfo = tb[n]
				errStr += "\n @ %s:%s:%d" % (os.path.basename(locationInfo[0]), locationInfo[2], locationInfo[1])
			if not self._shownError:
				wx.CallAfter(wx.MessageBox, errStr, '3D window error', wx.OK | wx.ICON_EXCLAMATION)
				self._shownError = True

	def _drawGui(self):
		if self._glButtonsTexture is None:
			self._glButtonsTexture = opengl.loadGLTexture('glButtons.png')
			self._glRobotTexture = opengl.loadGLTexture('UltimakerRobot.png')

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
		glBindTexture(GL_TEXTURE_2D, self._glRobotTexture)
		glEnable(GL_TEXTURE_2D)
		glPushMatrix()
		glColor4f(1,1,1,1)
		glTranslate(size.GetWidth() - 8,size.GetHeight() - 16,0)
		s = self._buttonSize * 1.4
		glScale(s,s,s)
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f(0,-1)
		glTexCoord2f(0, 0)
		glVertex2f(-1,-1)
		glTexCoord2f(0, 1)
		glVertex2f(-1, 0)
		glTexCoord2f(1, 1)
		glVertex2f(0, 0)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glPopMatrix()

	def _OnEraseBackground(self,event):
		#Workaround for windows background redraw flicker.
		pass

	def _OnSize(self,e):
		self._container.setSize(0, 0, self.GetSize().GetWidth(), self.GetSize().GetHeight())
		self._container.updateLayout()
		self.Refresh()

	def OnMouseLeftDown(self,e):
		pass
	def OnMouseLeftUp(self,e):
		pass
	def OnMouseMotion(self, e):
		pass
	def OnPaint(self, e):
		pass
	def OnKeyChar(self, keycode):
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
		gridSize = bs * 1.0
		for ctrl in self._parent._glGuiControlList:
			pos = ctrl._pos
			if pos[0] < 0:
				x = w + pos[0] * gridSize - bs * 0.2
			else:
				x = pos[0] * gridSize + bs * 0.2
			if pos[1] < 0:
				y = h + pos[1] * gridSize * 1.2 - bs * 0.2
			else:
				y = pos[1] * gridSize * 1.2 + bs * 0.2
			ctrl.setSize(x, y, gridSize, gridSize)

	def getLayoutSize(self):
		_, _, w, h = self._parent.getSize()
		return w, h

class glGuiLayoutGrid(object):
	def __init__(self, parent):
		self._parent = parent
		self._parent._layout = self
		self._size = 0,0
		self._alignBottom = True

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
		self._size = sum(widths.values()) + borderSize * 2, sum(heights.values()) + borderSize * 2
		if self._alignBottom:
			y0 -= self._size[1] - self._parent.getSize()[3]
			self._parent.setSize(x0 - borderSize, y0 - borderSize, self._size[0], self._size[1])
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
		self._showExpandArrow = False

	def setSelected(self, value):
		self._selected = value

	def setExpandArrow(self, value):
		self._showExpandArrow = value

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

		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
		scale = 0.8
		if self._selected:
			scale = 1.0
		elif self._focus:
			scale = 0.9
		if self._disabled:
			glColor4ub(128,128,128,128)
		else:
			glColor4ub(255,255,255,255)
		opengl.glDrawTexturedQuad(pos[0]-bs*scale/2, pos[1]-bs*scale/2, bs*scale, bs*scale, 0)
		opengl.glDrawTexturedQuad(pos[0]-bs*scale/2, pos[1]-bs*scale/2, bs*scale, bs*scale, self._imageID)
		if self._showExpandArrow:
			if self._selected:
				opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1)
			else:
				opengl.glDrawTexturedQuad(pos[0]+bs*scale/2-bs*scale/4*1.2, pos[1]-bs*scale/2*1.2, bs*scale/4, bs*scale/4, 1, 2)
		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		if self._focus:
			glTranslatef(0, -0.55*bs*scale, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, 2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(2, 0, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glTranslatef(0, -2, 0)
			opengl.glDrawStringCenter(self._tooltip)
			glPopMatrix()

			glColor4ub(255,255,255,255)
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
		self._base._focus = None
		for ctrl in self._group:
			if ctrl != self:
				ctrl.setSelected(False)
		if self.getSelected():
			self.setSelected(False)
		else:
			self.setSelected(True)
		self._radioCallback()

class glComboButton(glButton):
	def __init__(self, parent, tooltip, imageIDs, tooltips, pos, callback):
		super(glComboButton, self).__init__(parent, imageIDs[0], tooltip, pos, self._onComboOpenSelect)
		self._imageIDs = imageIDs
		self._tooltips = tooltips
		self._comboCallback = callback
		self._selection = 0

	def _onComboOpenSelect(self):
		if self.hasFocus():
			self._base._focus = None
		else:
			self._base._focus = self

	def draw(self):
		if self._hidden:
			return
		self._selected = self.hasFocus()
		super(glComboButton, self).draw()

		bs = self._base._buttonSize / 2
		pos = self._getPixelPos()

		if not self._selected:
			return

		glPushMatrix()
		glTranslatef(pos[0]+bs*0.5, pos[1] + bs*0.5, 0)
		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
		for n in xrange(0, len(self._imageIDs)):
			glTranslatef(0, bs, 0)
			glColor4ub(255,255,255,255)
			opengl.glDrawTexturedQuad(-0.5*bs,-0.5*bs,bs,bs, 0)
			opengl.glDrawTexturedQuad(-0.5*bs,-0.5*bs,bs,bs, self._imageIDs[n])
			glDisable(GL_TEXTURE_2D)

			glPushMatrix()
			glTranslatef(-0.55*bs, 0.1*bs, 0)

			glPushMatrix()
			glColor4ub(60,60,60,255)
			glTranslatef(-1, -1, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glTranslatef(0, 2, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glTranslatef(2, 0, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glTranslatef(0, -2, 0)
			opengl.glDrawStringRight(self._tooltips[n])
			glPopMatrix()

			glColor4ub(255,255,255,255)
			opengl.glDrawStringRight(self._tooltips[n])
			glPopMatrix()
		glPopMatrix()

	def getValue(self):
		return self._selection

	def setValue(self, value):
		self._selection = value
		self._imageID = self._imageIDs[self._selection]
		self._comboCallback()

	def OnMouseDown(self, x, y):
		if self._hidden or self._disabled:
			return False
		if self.hasFocus():
			bs = self._base._buttonSize / 2
			pos = self._getPixelPos()
			if 0 <= x - pos[0] <= bs and 0 <= y - pos[1] - bs <= bs * len(self._imageIDs):
				self._selection = int((y - pos[1] - bs) / bs)
				self._imageID = self._imageIDs[self._selection]
				self._base._focus = None
				self._comboCallback()
				return True
		return super(glComboButton, self).OnMouseDown(x, y)

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
		glBindTexture(GL_TEXTURE_2D, self._base._glButtonsTexture)
		glEnable(GL_TEXTURE_2D)

		size = self._layout.getLayoutSize()
		glColor4ub(255,255,255,255)
		glBegin(GL_QUADS)
		bs /= 2
		tc = 1 / 4 / 2

#		glTexCoord2f(1, 0)
#		glVertex2f( size[0], 0)
#		glTexCoord2f(0, 0)
#		glVertex2f( 0, 0)
#		glTexCoord2f(0, 1)
#		glVertex2f( 0, size[1])
#		glTexCoord2f(1, 1)
#		glVertex2f( size[0], size[1])
		#TopLeft
		glTexCoord2f(tc, 0)
		glVertex2f( bs, 0)
		glTexCoord2f(0, 0)
		glVertex2f( 0, 0)
		glTexCoord2f(0, tc/2)
		glVertex2f( 0, bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, bs)
		#TopRight
		glTexCoord2f(tc+tc, 0)
		glVertex2f( size[0], 0)
		glTexCoord2f(tc, 0)
		glVertex2f( size[0] - bs, 0)
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0] - bs, bs)
		glTexCoord2f(tc+tc, tc/2)
		glVertex2f( size[0], bs)
		#BottomLeft
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, size[1] - bs)
		glTexCoord2f(0, tc/2)
		glVertex2f( 0, size[1] - bs)
		glTexCoord2f(0, tc/2+tc/2)
		glVertex2f( 0, size[1])
		glTexCoord2f(tc, tc/2+tc/2)
		glVertex2f( bs, size[1])
		#BottomRight
		glTexCoord2f(tc+tc, tc/2)
		glVertex2f( size[0], size[1] - bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0] - bs, size[1] - bs)
		glTexCoord2f(tc, tc/2+tc/2)
		glVertex2f( size[0] - bs, size[1])
		glTexCoord2f(tc+tc, tc/2+tc/2)
		glVertex2f( size[0], size[1])

		#Center
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0]-bs, bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, size[1]-bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0]-bs, size[1]-bs)

		#Right
		glTexCoord2f(tc+tc, tc/2)
		glVertex2f( size[0], bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0]-bs, bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0]-bs, size[1]-bs)
		glTexCoord2f(tc+tc, tc/2)
		glVertex2f( size[0], size[1]-bs)

		#Left
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, bs)
		glTexCoord2f(0, tc/2)
		glVertex2f( 0, bs)
		glTexCoord2f(0, tc/2)
		glVertex2f( 0, size[1]-bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, size[1]-bs)

		#Top
		glTexCoord2f(tc, 0)
		glVertex2f( size[0]-bs, 0)
		glTexCoord2f(tc, 0)
		glVertex2f( bs, 0)
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0]-bs, bs)

		#Bottom
		glTexCoord2f(tc, tc/2)
		glVertex2f( size[0]-bs, size[1]-bs)
		glTexCoord2f(tc, tc/2)
		glVertex2f( bs, size[1]-bs)
		glTexCoord2f(tc, tc/2+tc/2)
		glVertex2f( bs, size[1])
		glTexCoord2f(tc, tc/2+tc/2)
		glVertex2f( size[0]-bs, size[1])

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

#		glColor4ub(255,255,255,128)
#		glBegin(GL_QUADS)
#		glTexCoord2f(1, 0)
#		glVertex2f( w, 0)
#		glTexCoord2f(0, 0)
#		glVertex2f( 0, 0)
#		glTexCoord2f(0, 1)
#		glVertex2f( 0, h)
#		glTexCoord2f(1, 1)
#		glVertex2f( w, h)
#		glEnd()

		glTranslate(5, h - 5, 0)
		glColor4ub(255,255,255,255)
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

		if self.hasFocus():
			glColor4ub(255,255,255,255)
		else:
			glColor4ub(255,255,255,192)
		glBegin(GL_QUADS)
		glTexCoord2f(1, 0)
		glVertex2f( w, 0)
		glTexCoord2f(0, 0)
		glVertex2f( 0, 0)
		glTexCoord2f(0, 1)
		glVertex2f( 0, h-1)
		glTexCoord2f(1, 1)
		glVertex2f( w, h-1)
		glEnd()

		glTranslate(5, h - 5, 0)
		glColor4ub(0,0,0,255)
		opengl.glDrawStringLeft(self._value)
		if self.hasFocus():
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
		if c == wx.WXK_TAB or c == wx.WXK_NUMPAD_ENTER or c == wx.WXK_RETURN:
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

		glColor3ub(255,255,255)
		if self._value:
			opengl.glDrawTexturedQuad(w/2-h/2,0, h, h, 28)
		else:
			opengl.glDrawTexturedQuad(w/2-h/2,0, h, h, 29)

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

class glSlider(glGuiControl):
	def __init__(self, parent, value, minValue, maxValue, pos, callback):
		super(glSlider, self).__init__(parent, pos)
		self._callback = callback
		self._focus = False
		self._hidden = False
		self._value = value
		self._minValue = minValue
		self._maxValue = maxValue

	def setValue(self, value):
		self._value = value
		self._value = max(self._minValue, self._value)
		self._value = min(self._maxValue, self._value)

	def getValue(self):
		return self._value

	def setRange(self, minValue, maxValue):
		if maxValue < minValue:
			maxValue = minValue
		self._minValue = minValue
		self._maxValue = maxValue
		self._value = max(minValue, self._value)
		self._value = min(maxValue, self._value)

	def getMinValue(self):
		return self._minValue

	def getMaxValue(self):
		return self._maxValue

	def setHidden(self, value):
		self._hidden = value

	def getMinSize(self):
		return self._base._buttonSize * 0.2, self._base._buttonSize * 4

	def _getPixelPos(self):
		x0, y0, w, h = self.getSize()
		minSize = self.getMinSize()
		return x0 + w / 2 - minSize[0] / 2, y0 + h / 2 - minSize[1] / 2

	def draw(self):
		if self._hidden:
			return

		w, h = self.getMinSize()
		pos = self._getPixelPos()

		glPushMatrix()
		glTranslatef(pos[0], pos[1], 0)
		glDisable(GL_TEXTURE_2D)
		if self.hasFocus():
			glColor4ub(60,60,60,255)
		else:
			glColor4ub(60,60,60,192)
		glBegin(GL_QUADS)
		glVertex2f( w/2,-h/2)
		glVertex2f(-w/2,-h/2)
		glVertex2f(-w/2, h/2)
		glVertex2f( w/2, h/2)
		glEnd()
		scrollLength = h - w
		glTranslate(0.0,scrollLength/2,0)
		if self._focus:
			glColor4ub(0,0,0,255)
			glPushMatrix()
			glTranslate(-w/2,opengl.glGetStringSize(str(self._minValue))[1]/2,0)
			opengl.glDrawStringRight(str(self._minValue))
			glTranslate(0,-scrollLength,0)
			opengl.glDrawStringRight(str(self._maxValue))
			if self._maxValue-self._minValue > 0:
				glTranslate(w,scrollLength-scrollLength*((self._value-self._minValue)/(self._maxValue-self._minValue)),0)
			opengl.glDrawStringLeft(str(self._value))
			glPopMatrix()
		glColor4ub(255,255,255,240)
		if self._maxValue - self._minValue != 0:
			glTranslate(0.0,-scrollLength*((self._value-self._minValue)/(self._maxValue-self._minValue)),0)
		glBegin(GL_QUADS)
		glVertex2f( w/2,-w/2)
		glVertex2f(-w/2,-w/2)
		glVertex2f(-w/2, w/2)
		glVertex2f( w/2, w/2)
		glEnd()
		glPopMatrix()

	def _checkHit(self, x, y):
		if self._hidden:
			return False
		pos = self._getPixelPos()
		w, h = self.getMinSize()
		return -w/2 <= x - pos[0] <= w/2 and -h/2 <= y - pos[1] <= h/2

	def setFocus(self):
		self._base._focus = self
		return True

	def OnMouseMotion(self, x, y):
		if self.hasFocus():
			w, h = self.getMinSize()
			scrollLength = h - w
			pos = self._getPixelPos()
			self.setValue(int(self._minValue + (self._maxValue - self._minValue) * -(y - pos[1] - scrollLength/2) / scrollLength))
			self._callback()
			return True
		if self._checkHit(x, y):
			self._focus = True
			return True
		self._focus = False
		return False

	def OnMouseDown(self, x, y):
		if self._checkHit(x, y):
			self.setFocus()
			self.OnMouseMotion(x, y)
			return True
		return False

	def OnMouseUp(self, x, y):
		if self.hasFocus():
			self._base._focus = None
			return True
		return False
