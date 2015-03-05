__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx

from Cura.gui import configBase
from Cura.util import profile

class expertConfigWindow(wx.Dialog):
	"Expert configuration window"
	def _addSettingsToPanels(self, category, sub_category, left, right):
		count = len(profile.getSubCategoriesFor(category)) + len(profile.getSettingsForCategory(category))

		p = left
		n = 0
		for title in profile.getSubCategoriesFor(category):
			if sub_category is not None and sub_category != title:
				continue
			n += 1 + len(profile.getSettingsForCategory(category, title))
			if n > count / 2:
				p = right
			configBase.TitleRow(p, _(title))
			for s in profile.getSettingsForCategory(category, title):
				if s.checkConditions():
					configBase.SettingRow(p, s.getName())

	def __init__(self, callback, sub_category=None):
		super(expertConfigWindow, self).__init__(None, title=_('Expert config'), style=wx.DEFAULT_DIALOG_STYLE)

		wx.EVT_CLOSE(self, self.OnClose)
		self.panel = configBase.configPanelBase(self, callback)

		left, right, main = self.panel.CreateConfigPanel(self)
		self._addSettingsToPanels('expert', sub_category, left, right)

		button_panel = right
		if sub_category is not None:
			button_panel = left
		self.okButton = wx.Button(button_panel, -1, 'Ok')
		button_panel.GetSizer().Add(self.okButton, (button_panel.GetSizer().GetRows(), 0), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=10)
		self.Bind(wx.EVT_BUTTON, lambda e: self.Close(), self.okButton)
		
		main.Fit()
		self.Fit()

	def OnClose(self, e):
		self.Destroy()
