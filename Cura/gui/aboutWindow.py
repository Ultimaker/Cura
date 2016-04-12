__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import wx.lib.scrolledpanel
import platform
from Cura.util import version

class aboutWindow(wx.Frame):
	def __init__(self, parent):
		super(aboutWindow, self).__init__(parent, title=_("About"), style = wx.DEFAULT_DIALOG_STYLE)

		wx.EVT_CLOSE(self, self.OnClose)

		p2 = wx.lib.scrolledpanel.ScrolledPanel(self,-1, size=(600, 300), style=wx.SIMPLE_BORDER)
		p2.SetBackgroundColour('#FFFFFF')
		s2 = wx.BoxSizer(wx.VERTICAL)
		p2.SetSizer(s2)
		p2.SetupScrolling()
		self.scrolledpanel = p2
		p = wx.Panel(self)
		self.panel = p
		s = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(s)
		s.Add(self.panel, flag=wx.ALL, border=15)
		s.Add(self.scrolledpanel, flag=wx.EXPAND|wx.ALL, border=5)
		s = wx.BoxSizer(wx.VERTICAL)
		p.SetSizer(s)

		title = wx.StaticText(p, -1, 'Cura LulzBot Edition')
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		s.Add(title, flag=wx.ALIGN_CENTRE|wx.EXPAND|wx.BOTTOM, border=5)

		version_num = version.getVersion()
		s.Add(wx.StaticText(p, -1, 'Version {}'.format(version_num)))

		s.Add(wx.StaticText(p, -1, 'Release notes:'))
		url = "code.alephobjects.com/w/cura/release-notes/"
		s.Add(wx.HyperlinkCtrl(p, -1, url, url))

		s.Add(wx.StaticText(p, -1, 'Source Code:'))
		url2 = "code.alephobjects.com/diffusion/CURA/"
		s.Add(wx.HyperlinkCtrl(p, -1, url2, url2))

		s.Add(wx.StaticText(p, -1, ''))
		s.Add(wx.StaticText(p, -1, 'End solution for Free Software Fused Filament Fabrication 3D printing.'), flag=wx.TOP, border=5)
		s.Add(wx.StaticText(p, -1, 'Cura LulzBot Edition is maintained by Aleph Objects, Inc. for use with'), flag=wx.TOP, border=5)
		s.Add(wx.StaticText(p, -1, 'LulzBot 3D printers. It is derived from Cura, which was created'))
		s.Add(wx.StaticText(p, -1, 'by David Braam and Ultimaker.'))

		s2.Add(wx.StaticText(p2, -1, 'Cura is built with the following components:'), flag=wx.TOP, border=10)
		self.addComponent('Cura', 'Graphical user interface', 'AGPLv3', 'https://github.com/daid/Cura')
		self.addComponent('CuraEngine', 'GCode Generator', 'AGPLv3', 'https://github.com/Ultimaker/CuraEngine')
		self.addComponent('Clipper', 'Polygon clipping library', 'Boost', 'http://www.angusj.com/delphi/clipper.php')

		self.addComponent('Python 2.7', 'Framework', 'Python', 'http://python.org/')
		self.addComponent('wxPython', 'GUI Framework', 'wxWindows', 'http://www.wxpython.org/')
		self.addComponent('PyOpenGL', '3D Rendering Framework', 'BSD', 'http://pyopengl.sourceforge.net/')
		self.addComponent('PySerial', 'Serial communication library', 'Python license', 'http://pyserial.sourceforge.net/')
		self.addComponent('NumPy', 'Support library for faster math', 'BSD', 'http://www.numpy.org/')
		if platform.system() == "Windows":
			self.addComponent('VideoCapture', 'Library for WebCam capture on windows', 'LGPLv2.1', 'http://videocapture.sourceforge.net/')
			#self.addComponent('ffmpeg', 'Support for making timelaps video files', 'GPL', 'http://www.ffmpeg.org/')
			self.addComponent('comtypes', 'Library to help with windows taskbar features on Windows 7', 'MIT', 'http://starship.python.net/crew/theller/comtypes/')
			self.addComponent('EjectMedia', 'Utility to safe-remove SD cards', 'Freeware', 'http://www.uwe-sieber.de/english.html')
		self.addComponent('Pymclevel', 'Python library for reading Minecraft levels.', 'ISC', 'https://github.com/mcedit/pymclevel')
		
		s2.Add(wx.StaticText(p2, -1, ""))
		s2.Add(wx.StaticText(p2, -1, "Cura utilizes graphics from:"))
		self.addComponent('3d-printer', 'by Toke Frello', 'CC BY 3.0 US', 'https://thenounproject.com/term/3d-printer/170216/')
		self.addComponent('Check Mark', 'by Stefan Parnarov', 'CC BY 3.0', 'https://thenounproject.com/term/check-mark/63794/')
		
		s2.Add(wx.StaticText(p2, -1, "Copyright (C) 2014, 2015, 2016 Aleph Objects, Inc."), flag=wx.TOP, border=10)
		s2.Add(wx.StaticText(p2, -1, " - Released under terms of the AGPLv3 License"))
		s2.Add(wx.StaticText(p2, -1, "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"))
		#Translations done by:
		#Dutch: Charlotte Jansen
		#German: Gregor Luetolf, Lars Potter
		#Polish: Piotr Paczynski
		#French: Jeremie Francois
		#Spanish: Jose Gemez
		self.Fit()

	def addComponent(self, name, description, license, url):
		p = self.scrolledpanel
		s = p.GetSizer()
		s.Add(wx.StaticText(p, -1, '* %s - %s' % (name, description)), flag=wx.TOP, border=5)
		s.Add(wx.StaticText(p, -1, '   License: %s - Website: %s' % (license, url)))

	def OnClose(self, e):
		self.Destroy()
