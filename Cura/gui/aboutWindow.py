__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx
import platform

class aboutWindow(wx.Dialog):
	def __init__(self):
		super(aboutWindow, self).__init__(None, title="About")

		wx.EVT_CLOSE(self, self.OnClose)

		p = wx.Panel(self)
		self.panel = p
		s = wx.BoxSizer()
		self.SetSizer(s)
		s.Add(p, flag=wx.ALL, border=15)
		s = wx.BoxSizer(wx.VERTICAL)
		p.SetSizer(s)

		title = wx.StaticText(p, -1, 'Cura')
		title.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
		s.Add(title, flag=wx.ALIGN_CENTRE|wx.EXPAND|wx.BOTTOM, border=5)

		s.Add(wx.StaticText(p, -1, 'End solution for Open Source Fused Filament Fabrication 3D printing.'))
		s.Add(wx.StaticText(p, -1, 'Cura is currently developed and maintained by Ultimaker.'))

		s.Add(wx.StaticText(p, -1, 'Cura is build with the following components:'), flag=wx.TOP, border=10)
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
			self.addComponent('ffmpeg', 'Support for making timelaps video files', 'GPL', 'http://www.ffmpeg.org/')
			self.addComponent('comtypes', 'Library to help with windows taskbar features on Windows 7', 'MIT', 'http://starship.python.net/crew/theller/comtypes/')
			self.addComponent('EjectMedia', 'Utility to safe-remove SD cards', 'Freeware', 'http://www.uwe-sieber.de/english.html')
		self.addComponent('Pymclevel', 'Python library for reading Minecraft levels.', 'ISC', 'https://github.com/mcedit/pymclevel')

		#Translations done by:
		#Dutch: Charlotte Jansen
		#German: Gregor Luetolf
		#Polish: Piotr Paczynski
		#French: Jeremie Francois
		#Spanish: Jose Gemez
		self.Fit()

	def addComponent(self, name, description, license, url):
		p = self.panel
		s = p.GetSizer()
		s.Add(wx.StaticText(p, -1, '* %s - %s' % (name, description)), flag=wx.TOP, border=5)
		s.Add(wx.StaticText(p, -1, '   License: %s - Website: %s' % (license, url)))

	def OnClose(self, e):
		self.Destroy()

# 		info = wx.AboutDialogInfo()
# 		info.SetName("Cura")
# 		info.SetDescription("""
# End solution for Open Source Fused Filament Fabrication 3D printing.
# * Cura is the graphical User Interface.
# * CuraEngine is the slicer/gcode generator.
# Cura and the CuraEngine are licensed AGPLv3.
# 		""")
# 		info.SetWebSite('http://software.ultimaker.com/')
# 		info.SetCopyright(_("Copyright (C) David Braam"))
# 		info.SetLicence("""
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
# """)
# 		wx.AboutBox(info)
