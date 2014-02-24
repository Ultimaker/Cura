__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.gui import configBase
from Cura.util import profile

class expertConfigWindow(wx.Dialog):
	"Expert configuration window"
	def _addSettingsToPanels(self, category, left, right):
		count = len(profile.getSubCategoriesFor(category)) + len(profile.getSettingsForCategory(category))

		p = left
		n = 0
		for title in profile.getSubCategoriesFor(category):
			n += 1 + len(profile.getSettingsForCategory(category, title))
			if n > count / 2:
				p = right
			configBase.TitleRow(p, title)
			for s in profile.getSettingsForCategory(category, title):
				if s.checkConditions():
					configBase.SettingRow(p, s.getName())

	def __init__(self, callback):
		super(expertConfigWindow, self).__init__(None, title='Expert config', style=wx.DEFAULT_DIALOG_STYLE)

		wx.EVT_CLOSE(self, self.OnClose)
		self.panel = configBase.configPanelBase(self, callback)

		left, right, main = self.panel.CreateConfigPanel(self)
		self._addSettingsToPanels('expert', left, right)

		self.okButton = wx.Button(right, -1, 'Ok')
		right.GetSizer().Add(self.okButton, (right.GetSizer().GetRows(), 0))
		self.Bind(wx.EVT_BUTTON, lambda e: self.Close(), self.okButton)
		
		main.Fit()
		self.Fit()

	def OnClose(self, e):
		self.Destroy()
