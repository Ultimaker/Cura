__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import numpy

from Cura.util import printableObject

def supportedExtensions():
	return ['.bmp', '.jpg', '.jpeg', '.png']

class convertImageDialog(wx.Dialog):
	def __init__(self, parent, filename):
		super(convertImageDialog, self).__init__(None, title="Convert image...")
		wx.EVT_CLOSE(self, self.OnClose)
		self.parent = parent
		self.filename = filename

		image = wx.Image(filename)
		w, h = image.GetWidth() - 1, image.GetHeight() - 1
		self.aspectRatio = float(w) / float(h)

		p = wx.Panel(self)
		self.SetSizer(wx.BoxSizer())
		self.GetSizer().Add(p, 1, flag=wx.EXPAND)

		s = wx.GridBagSizer(2, 2)
		p.SetSizer(s)
		s.Add(wx.StaticText(p, -1, _('Height (mm)')), pos=(0, 0), flag=wx.LEFT|wx.TOP|wx.RIGHT, border=5)
		self.heightInput = wx.TextCtrl(p, -1, '10.0')
		s.Add(self.heightInput, pos=(0, 1), flag=wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, border=5)

		s.Add(wx.StaticText(p, -1, _('Base (mm)')), pos=(1, 0), flag=wx.LEFT|wx.TOP|wx.RIGHT, border=5)
		self.baseHeightInput = wx.TextCtrl(p, -1, '1.0')
		s.Add(self.baseHeightInput, pos=(1, 1), flag=wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, border=5)

		s.Add(wx.StaticText(p, -1, _('Width (mm)')), pos=(2, 0), flag=wx.LEFT|wx.TOP|wx.RIGHT, border=5)
		self.widthInput = wx.TextCtrl(p, -1, str(w * 0.3))
		s.Add(self.widthInput, pos=(2, 1), flag=wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, border=5)

		s.Add(wx.StaticText(p, -1, _('Depth (mm)')), pos=(3, 0), flag=wx.LEFT|wx.TOP|wx.RIGHT, border=5)
		self.depthInput = wx.TextCtrl(p, -1, str(h * 0.3))
		s.Add(self.depthInput, pos=(3, 1), flag=wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, border=5)

		options = ['Darker is higher', 'Lighter is higher']
		self.invertInput = wx.ComboBox(p, -1, options[0], choices=options, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		s.Add(self.invertInput, pos=(4, 1), flag=wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, border=5)
		self.invertInput.SetSelection(0)

		options = ['No smoothing', 'Light smoothing', 'Heavy smoothing']
		self.smoothInput = wx.ComboBox(p, -1, options[0], choices=options, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		s.Add(self.smoothInput, pos=(5, 1), flag=wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND, border=5)
		self.smoothInput.SetSelection(0)

		self.okButton = wx.Button(p, -1, 'Ok')
		s.Add(self.okButton, pos=(6, 1), flag=wx.ALL, border=5)

		self.okButton.Bind(wx.EVT_BUTTON, self.OnOkClick)
		self.widthInput.Bind(wx.EVT_TEXT, self.OnWidthEnter)
		self.depthInput.Bind(wx.EVT_TEXT, self.OnDepthEnter)

		self.Fit()
		self.Centre()

	def OnClose(self, e):
		self.Destroy()

	def OnOkClick(self, e):
		self.Close()
		height = float(self.heightInput.GetValue())
		width = float(self.widthInput.GetValue())
		blur = self.smoothInput.GetSelection()
		blur *= blur
		invert = self.invertInput.GetSelection() == 0
		baseHeight = float(self.baseHeightInput.GetValue())

		obj = convertImage(self.filename, height, width, blur, invert, baseHeight)
		self.parent._scene.add(obj)
		self.parent._scene.centerAll()
		self.parent.sceneUpdated()

	def OnWidthEnter(self, e):
		try:
			w = float(self.widthInput.GetValue())
		except ValueError:
			return
		h = w / self.aspectRatio
		self.depthInput.SetValue(str(h))

	def OnDepthEnter(self, e):
		try:
			h = float(self.depthInput.GetValue())
		except ValueError:
			return
		w = h * self.aspectRatio
		self.widthInput.SetValue(str(w))

def convertImage(filename, height=20.0, width=100.0, blur=0, invert=False, baseHeight=1.0):
	image = wx.Image(filename)
	image.ConvertToGreyscale()
	if image.GetHeight() > 512:
		image.Rescale(image.GetWidth() * 512 / image.GetHeight(), 512, wx.IMAGE_QUALITY_HIGH)
	if image.GetWidth() > 512:
		image.Rescale(512, image.GetHeight() * 512 / image.GetWidth(), wx.IMAGE_QUALITY_HIGH)
	if blur > 0:
		image = image.Blur(blur)
	z = numpy.fromstring(image.GetData(), numpy.uint8)
	z = numpy.array(z[::3], numpy.float32)	#Only get the R values (as we are grayscale), and convert to float values
	if invert:
		z = 255 - z
	pMin, pMax = numpy.min(z), numpy.max(z)
	if pMax == pMin:
		pMax += 1.0
	z = ((z - pMin) * height / (pMax - pMin)) + baseHeight

	w, h = image.GetWidth(), image.GetHeight()
	scale = width / (image.GetWidth() - 1)
	n = w * h
	y, x = numpy.mgrid[0:h,0:w]
	x = numpy.array(x, numpy.float32, copy=False) * scale
	y = numpy.array(y, numpy.float32, copy=False) *-scale
	v0 = numpy.concatenate((x.reshape((n, 1)), y.reshape((n, 1)), z.reshape((n, 1))), 1)
	v0 = v0.reshape((h, w, 3))
	v1 = v0[0:-1,0:-1,:]
	v2 = v0[0:-1,1:,:]
	v3 = v0[1:,0:-1,:]
	v4 = v0[1:,1:,:]

	obj = printableObject.printableObject(filename)
	m = obj._addMesh()
	m._prepareFaceCount((w-1) * (h-1) * 2 + 2 + (w-1)*4 + (h-1)*4)
	m.vertexes = numpy.array(numpy.concatenate((v1,v3,v2,v2,v3,v4), 2).reshape(((w-1) * (h-1) * 6, 3)), numpy.float32, copy=False)
	m.vertexes = numpy.concatenate((m.vertexes, numpy.zeros(((2+(w-1)*4+(h-1)*4)*3, 3), numpy.float32)))
	m.vertexCount = (w-1) * (h-1) * 6
	x = (w-1)* scale
	y = (h-1)*-scale
	m._addFace(0,0,0, x,0,0, 0,y,0)
	m._addFace(x,y,0, 0,y,0, x,0,0)
	for n in xrange(0, w-1):
		x = n* scale
		i = w*h-w+n
		m._addFace(x+scale,0,0, x,0,0, x,0,z[n])
		m._addFace(x+scale,0,0, x,0,z[n], x+scale,0,z[n+1])
		m._addFace(x+scale,y,0, x,y,z[i], x,y,0)
		m._addFace(x+scale,y,0, x+scale,y,z[i+1], x,y,z[i])

	x = (w-1)*scale
	for n in xrange(0, h-1):
		y = n*-scale
		i = n*w+w-1
		m._addFace(0,y-scale,0, 0,y,z[n*w], 0,y,0)
		m._addFace(0,y-scale,0, 0,y-scale,z[n*w+w], 0,y,z[n*w])
		m._addFace(x,y-scale,0, x,y,0, x,y,z[i])
		m._addFace(x,y-scale,0, x,y,z[i], x,y-scale,z[i+w])
	obj._postProcessAfterLoad()
	return obj
