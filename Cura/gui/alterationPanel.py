__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import wx, wx.stc

from Cura.gui.util import gcodeTextArea
from Cura.util import profile
#Panel to change the start & endcode of the gcode.
class alterationPanel(wx.Panel):
	def __init__(self, parent, callback):
		wx.Panel.__init__(self, parent,-1)

		self.callback = callback
		self.alterationFileList = ['start.gcode', 'end.gcode']#, 'nextobject.gcode', 'replace.csv'
		if int(profile.getMachineSetting('extruder_amount')) > 1:
			self.alterationFileList += ['preSwitchExtruder.gcode', 'postSwitchExtruder.gcode']
			self.alterationFileList += ['start2.gcode', 'end2.gcode']
		if int(profile.getMachineSetting('extruder_amount')) > 2:
			self.alterationFileList += ['start3.gcode', 'end3.gcode']
		if int(profile.getMachineSetting('extruder_amount')) > 3:
			self.alterationFileList += ['start4.gcode', 'end4.gcode']
		self.currentFile = None

		self.textArea = gcodeTextArea.GcodeTextArea(self)
		self.list = wx.ListBox(self, choices=self.alterationFileList, style=wx.LB_SINGLE)
		self.list.SetSelection(0)
		self.Bind(wx.EVT_LISTBOX, self.OnSelect, self.list)
		self.textArea.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost, self.textArea)
		self.textArea.Bind(wx.stc.EVT_STC_CHANGE, self.OnFocusLost, self.textArea)
		
		sizer = wx.GridBagSizer()
		sizer.Add(self.list, (0,0), span=(5,1), flag=wx.EXPAND)
		sizer.Add(self.textArea, (5,0), span=(5,1), flag=wx.EXPAND)
		sizer.AddGrowableCol(0)
		sizer.AddGrowableRow(0)
		sizer.AddGrowableRow(5)
		sizer.AddGrowableRow(6)
		sizer.AddGrowableRow(7)
		self.SetSizer(sizer)
		
		self.loadFile(self.alterationFileList[self.list.GetSelection()])
		self.currentFile = self.list.GetSelection()

	def OnSelect(self, e):
		self.loadFile(self.alterationFileList[self.list.GetSelection()])
		self.currentFile = self.list.GetSelection()

	def loadFile(self, filename):
		self.textArea.SetValue(profile.getAlterationFile(filename))

	def OnFocusLost(self, e):
		if self.currentFile == self.list.GetSelection():
			profile.setAlterationFile(self.alterationFileList[self.list.GetSelection()], self.textArea.GetValue())
			self.callback()

	def updateProfileToControls(self):
		self.OnSelect(None)
