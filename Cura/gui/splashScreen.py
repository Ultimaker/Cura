__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx._core #We only need the core here, which speeds up the import. As we want to show the splashscreen ASAP.

from Cura.util.resources import getPathForImage

class splashScreen(wx.SplashScreen):
	def __init__(self, callback):
		self.callback = callback
		bitmap = wx.Bitmap(getPathForImage('splash.png'))
		super(splashScreen, self).__init__(bitmap, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, 100, None)
		# Add a timeout and call the callback in the close event to avoid having the callback called
		# before the splashscreen paint events which could cause it not to appear or to appear as a grey
		# rectangle while the app is loading
		self.Bind(wx.EVT_CLOSE, self.OnClose)


	def OnClose(self, e):
		if self.callback:
			# Avoid calling the callback twice
			cb = self.callback
			self.callback = None
			# The callback will destroy us
			wx.CallAfter(cb)

		e.Skip()
