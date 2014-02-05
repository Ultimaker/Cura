"""
Tool to import sections of minecraft levels into Cura.
This makes use of the pymclevel module from David Rio Vierra
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import glob
import os
import numpy

from Cura.util import printableObject
from Cura.util.meshLoaders import stl
from Cura.util.pymclevel import mclevel

def hasMinecraft():
	return os.path.isdir(mclevel.saveFileDir)

class minecraftImportWindow(wx.Frame):
	def __init__(self, parent):
		super(minecraftImportWindow, self).__init__(parent, title='Cura - Minecraft import')

		saveFileList = map(os.path.basename, glob.glob(mclevel.saveFileDir + "/*"))

		self.panel = wx.Panel(self, -1)
		self.SetSizer(wx.BoxSizer())
		self.GetSizer().Add(self.panel, 1, wx.EXPAND)

		sizer = wx.GridBagSizer(2, 2)

		self.saveListBox = wx.ListBox(self.panel, -1, choices=saveFileList)
		sizer.Add(self.saveListBox, (0,0), span=(2,1), flag=wx.EXPAND)
		self.playerListBox = wx.ListBox(self.panel, -1, choices=[])
		sizer.Add(self.playerListBox, (0,1), span=(2,1), flag=wx.EXPAND)

		self.previewPanel = wx.Panel(self.panel, -1)
		self.previewPanel.SetMinSize((512, 512))
		sizer.Add(self.previewPanel, (0,2), flag=wx.EXPAND)

		self.importButton = wx.Button(self.panel, -1, 'Import')
		sizer.Add(self.importButton, (1,2))

		sizer.AddGrowableRow(1)

		self.panel.SetSizer(sizer)

		self.saveListBox.Bind(wx.EVT_LISTBOX, self.OnSaveSelect)
		self.playerListBox.Bind(wx.EVT_LISTBOX, self.OnPlayerSelect)
		self.importButton.Bind(wx.EVT_BUTTON, self.OnImport)

		self.previewPanel.Bind(wx.EVT_PAINT, self.OnPaintPreview)
		self.previewPanel.Bind(wx.EVT_SIZE, self.OnSizePreview)
		self.previewPanel.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackgroundPreview)
		self.previewPanel.Bind(wx.EVT_MOTION, self.OnMotion)

		self.level = None
		self.previewImage = None
		self.renderList = []
		self.selectArea = None
		self.draggingArea = False

		self.Layout()
		self.Fit()

		self.gravelPen = wx.Pen(wx.Colour(128, 128, 128))
		self.sandPen = wx.Pen(wx.Colour(192, 192, 0))
		self.grassPen = []
		self.waterPen = []
		for z in xrange(0, 256):
			self.waterPen.append(wx.Pen(wx.Colour(0,0,min(z+64, 255))))
			self.grassPen.append(wx.Pen(wx.Colour(0,min(64+z,255),0)))

		self.isSolid = [True] * 256
		self.isSolid[0] = False #Air
		self.isSolid[8] = False #Water
		self.isSolid[9] = False #Water
		self.isSolid[10] = False #Lava
		self.isSolid[11] = False #Lava
		self.isSolid[50] = False #Torch
		self.isSolid[51] = False #Fire

	def OnSaveSelect(self, e):
		if self.saveListBox.Selection < 0:
			return
		self.level = mclevel.loadWorld(self.saveListBox.GetItems()[self.saveListBox.Selection])
		self.playerListBox.Clear()
		for player in self.level.players:
			self.playerListBox.Append(player)

	def OnPlayerSelect(self, e):
		playerName = self.playerListBox.GetItems()[self.playerListBox.Selection]
		self.playerPos = map(lambda n: int(n / 16), self.level.getPlayerPosition(playerName))[0::2]

		self.previewImage = wx.EmptyBitmap(512, 512)
		for i in xrange(0, 16):
			for j in xrange(1, i * 2 + 1):
				self.renderList.insert(0, (15 - i, 16 + i - j))
			for j in xrange(0, i * 2 + 1):
				self.renderList.insert(0, (15 + j - i, 15 - i))
			for j in xrange(0, i * 2 + 1):
				self.renderList.insert(0, (16 + i, 15 + j - i))
			for j in xrange(0, i * 2 + 2):
				self.renderList.insert(0, (16 + i - j, 16 + i))
		self.previewPanel.Refresh()

	def OnPaintPreview(self, e):
		if len(self.renderList) > 0:
			cx, cy = self.renderList.pop()
			dc = wx.MemoryDC()
			dc.SelectObject(self.previewImage)
			chunk = self.level.getChunk(cx + self.playerPos[0] - 16, cy + self.playerPos[1] - 16)
			dc.SetPen(wx.Pen(wx.Colour(255,0,0)))
			for x in xrange(0, 16):
				for y in xrange(0, 16):
					z = numpy.max(numpy.where(chunk.Blocks[x, y] != 0))
					type = chunk.Blocks[x, y, z]
					if type == 1:    #Stone
						dc.SetPen(wx.Pen(wx.Colour(z,z,z)))
					elif type == 2:    #Grass
						dc.SetPen(self.grassPen[z])
					elif type == 8 or type == 9: #Water
						dc.SetPen(self.waterPen[z])
					elif type == 10 or type == 11: #Lava
						dc.SetPen(wx.Pen(wx.Colour(min(z+64, 255),0,0)))
					elif type == 12 or type == 24: #Sand/Standstone
						dc.SetPen(self.sandPen)
					elif type == 13: #Gravel
						dc.SetPen(self.gravelPen)
					elif type == 18: #Leaves
						dc.SetPen(wx.Pen(wx.Colour(0,max(z-32, 0),0)))
					else:
						dc.SetPen(wx.Pen(wx.Colour(z,z,z)))
					dc.DrawPoint(cx * 16 + x, cy * 16 + y)
			dc.SelectObject(wx.NullBitmap)
			wx.CallAfter(self.previewPanel.Refresh)

		dc = wx.BufferedPaintDC(self.previewPanel)
		dc.SetBackground(wx.Brush(wx.BLACK))
		dc.Clear()
		if self.previewImage is not None:
			dc.DrawBitmap(self.previewImage, 0, 0)
		if self.selectArea is not None:
			dc.SetPen(wx.Pen(wx.Colour(255,0,0)))
			dc.SetBrush(wx.Brush(None, style=wx.TRANSPARENT))
			dc.DrawRectangle(self.selectArea[0], self.selectArea[1], self.selectArea[2] - self.selectArea[0] + 1, self.selectArea[3] - self.selectArea[1] + 1)

	def OnSizePreview(self, e):
		self.previewPanel.Refresh()
		self.previewPanel.Update()

	def OnEraseBackgroundPreview(self, e):
		pass

	def OnMotion(self, e):
		if e.Dragging():
			if not self.draggingArea:
				self.draggingArea = True
				self.selectArea = [e.GetX(), e.GetY(), e.GetX(), e.GetY()]
			self.selectArea[2] = e.GetX()
			self.selectArea[3] = e.GetY()
			self.previewPanel.Refresh()
		else:
			self.draggingArea = False

	def OnImport(self, e):
		if self.level is None or self.selectArea is None:
			return

		xMin = min(self.selectArea[0], self.selectArea[2]) + (self.playerPos[0] - 16) * 16
		xMax = max(self.selectArea[0], self.selectArea[2]) + (self.playerPos[0] - 16) * 16
		yMin = min(self.selectArea[1], self.selectArea[3]) + (self.playerPos[1] - 16) * 16
		yMax = max(self.selectArea[1], self.selectArea[3]) + (self.playerPos[1] - 16) * 16

		sx = (xMax - xMin + 1)
		sy = (yMax - yMin + 1)
		blocks = numpy.zeros((sx, sy, 256), numpy.int32)

		cxMin = int(xMin / 16)
		cxMax = int((xMax + 15) / 16)
		cyMin = int(yMin / 16)
		cyMax = int((yMax + 15) / 16)

		for cx in xrange(cxMin, cxMax + 1):
			for cy in xrange(cyMin, cyMax + 1):
				chunk = self.level.getChunk(cx, cy)
				for x in xrange(0, 16):
					bx = x + cx * 16
					if xMin <= bx <= xMax:
						for y in xrange(0, 16):
							by = y + cy * 16
							if yMin <= by <= yMax:
								blocks[bx - xMin, by - yMin] = chunk.Blocks[x, y]
		minZ = 256
		maxZ = 0
		for x in xrange(0, sx):
			for y in xrange(0, sy):
				minZ = min(minZ, numpy.max(numpy.where(blocks[x, y] != 0)))
				maxZ = max(maxZ, numpy.max(numpy.where(blocks[x, y] != 0)))
		minZ += 1

		faceCount = 0
		for x in xrange(0, sx):
			for y in xrange(0, sy):
				for z in xrange(minZ, maxZ + 1):
					if self.isSolid[blocks[x, y, z]]:
						if z == maxZ or not self.isSolid[blocks[x, y, z + 1]]:
							faceCount += 1
						if z == minZ or not self.isSolid[blocks[x, y, z - 1]]:
							faceCount += 1
						if x == 0 or not self.isSolid[blocks[x - 1, y, z]]:
							faceCount += 1
						if x == sx - 1 or not self.isSolid[blocks[x + 1, y, z]]:
							faceCount += 1
						if y == 0 or not self.isSolid[blocks[x, y - 1, z]]:
							faceCount += 1
						if y == sy - 1 or not self.isSolid[blocks[x, y + 1, z]]:
							faceCount += 1

		obj = printableObject.printableObject(None)
		m = obj._addMesh()
		m._prepareFaceCount(faceCount * 2)
		for x in xrange(0, sx):
			for y in xrange(0, sy):
				for z in xrange(minZ, maxZ + 1):
					if self.isSolid[blocks[x, y, z]]:
						if z == maxZ or not self.isSolid[blocks[x, y, z + 1]]:
							m._addFace(x, y, z+1, x+1, y, z+1, x, y+1, z+1)

							m._addFace(x+1, y+1, z+1, x, y+1, z+1, x+1, y, z+1)

						if z == minZ or not self.isSolid[blocks[x, y, z - 1]]:
							m._addFace(x, y, z, x, y+1, z, x+1, y, z)

							m._addFace(x+1, y+1, z, x+1, y, z, x, y+1, z)

						if x == 0 or not self.isSolid[blocks[x - 1, y, z]]:
							m._addFace(x, y, z, x, y, z+1, x, y+1, z)

							m._addFace(x, y+1, z+1, x, y+1, z, x, y, z+1)

						if x == sx - 1 or not self.isSolid[blocks[x + 1, y, z]]:
							m._addFace(x+1, y, z, x+1, y+1, z, x+1, y, z+1)

							m._addFace(x+1, y+1, z+1, x+1, y, z+1, x+1, y+1, z)

						if y == 0 or not self.isSolid[blocks[x, y - 1, z]]:
							m._addFace(x, y, z, x+1, y, z, x, y, z+1)

							m._addFace(x+1, y, z+1, x, y, z+1, x+1, y, z)

						if y == sy - 1 or not self.isSolid[blocks[x, y + 1, z]]:
							m._addFace(x, y+1, z, x, y+1, z+1, x+1, y+1, z)

							m._addFace(x+1, y+1, z+1, x+1, y+1, z, x, y+1, z+1)

		obj._postProcessAfterLoad()
		self.GetParent().scene._scene.add(obj)
