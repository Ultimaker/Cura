__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
from __future__ import absolute_import

import wx, os, multiprocessing, threading, time, shutil

from Cura.util import profile
from Cura.util import sliceRun
from Cura.util import meshLoader
from Cura.util import gcodeInterpreter
from Cura.gui.util import dropTarget

class batchRunWindow(wx.Frame):
	def __init__(self, parent):
		super(batchRunWindow, self).__init__(parent, title=_("Cura - Batch run"))
		
		self.list = []
		
		self.SetDropTarget(dropTarget.FileDropTarget(self.OnDropFiles, meshLoader.loadSupportedExtensions() + ['.g', '.gcode']))
		
		wx.EVT_CLOSE(self, self.OnClose)
		self.panel = wx.Panel(self, -1)
		self.SetSizer(wx.BoxSizer(wx.VERTICAL))
		self.GetSizer().Add(self.panel, 1, flag=wx.EXPAND)

		self.sizer = wx.GridBagSizer(2,2)
		self.panel.SetSizer(self.sizer)

		self.listbox = wx.ListBox(self.panel, -1, choices=[])
		self.addButton = wx.Button(self.panel, -1, _("Add"))
		self.remButton = wx.Button(self.panel, -1, _("Remove"))
		self.sliceButton = wx.Button(self.panel, -1, _("Prepare all"))

		self.addButton.Bind(wx.EVT_BUTTON, self.OnAddModel)
		self.remButton.Bind(wx.EVT_BUTTON, self.OnRemModel)
		self.sliceButton.Bind(wx.EVT_BUTTON, self.OnSlice)
		self.listbox.Bind(wx.EVT_LISTBOX, self.OnListSelect)

		self.sizer.Add(self.listbox, (0,0), span=(1,3), flag=wx.EXPAND)
		self.sizer.Add(self.addButton, (1,0), span=(1,1))
		self.sizer.Add(self.remButton, (1,1), span=(1,1))
		self.sizer.Add(self.sliceButton, (1,2), span=(1,1))

		self.sizer.AddGrowableCol(2)
		self.sizer.AddGrowableRow(0)

	def OnAddModel(self, e):
		dlg=wx.FileDialog(self, _("Open file to batch prepare"), os.path.split(profile.getPreference('lastFile'))[0], style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_MULTIPLE)
		dlg.SetWildcard("STL files (*.stl)|*.stl;*.STL")
		if dlg.ShowModal() == wx.ID_OK:
			for filename in dlg.GetPaths():
				profile.putPreference('lastFile', filename)
				self.list.append(filename)
				self.selection = filename
				self._updateListbox()
		dlg.Destroy()
	
	def OnDropFiles(self, filenames):
		for filename in filenames:
			profile.putPreference('lastFile', filename)
			self.list.append(filename)
			self.selection = filename
			self._updateListbox()

	def OnRemModel(self, e):
		if self.selection is None:
			return
		self.list.remove(self.selection)
		self._updateListbox()

	def OnListSelect(self, e):
		if self.listbox.GetSelection() == -1:
			return
		self.selection = self.list[self.listbox.GetSelection()]

	def _updateListbox(self):
		self.listbox.Clear()
		for item in self.list:
			self.listbox.AppendAndEnsureVisible(os.path.split(item)[1])
		if self.selection in self.list:
			self.listbox.SetSelection(self.list.index(self.selection))
		elif len(self.list) > 0:
			self.selection = self.list[0]
			self.listbox.SetSelection(0)
		else:
			self.selection = None
			self.listbox.SetSelection(-1)

	def OnClose(self, e):
		self.Destroy()

	def OnSlice(self, e):
		sliceCmdList = []
		outputFilenameList = []
		center = profile.getMachineCenterCoords() + profile.getObjectMatrix()
		for filename in self.list:
			outputFilename = sliceRun.getExportFilename(filename)
			outputFilenameList.append(outputFilename)
			sliceCmdList.append(sliceRun.getSliceCommand(outputFilename, [filename], [center]))
		bspw = BatchSliceProgressWindow(self.list[:], outputFilenameList, sliceCmdList)
		bspw.Centre()
		bspw.Show(True)
	
class BatchSliceProgressWindow(wx.Frame):
	def __init__(self, filenameList, outputFilenameList, sliceCmdList):
		super(BatchSliceProgressWindow, self).__init__(None, title='Cura')
		self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
		
		self.filenameList = filenameList
		self.outputFilenameList = outputFilenameList
		self.sliceCmdList = sliceCmdList
		self.abort = False
		self.sliceStartTime = time.time()

		try:
			self.threadCount = multiprocessing.cpu_count() - 1
		except:
			self.threadCount = 1
		if self.threadCount < 1:
			self.threadCount = 1
		if self.threadCount > len(self.sliceCmdList):
			self.threadCount = len(self.sliceCmdList)
		self.cmdIndex = 0
		
		self.prevStep = []
		self.totalDoneFactor = []
		for i in xrange(0, self.threadCount):
			self.prevStep.append('start')
			self.totalDoneFactor.append(0.0)

		self.sizer = wx.GridBagSizer(2, 2) 
		self.progressGauge = []
		self.statusText = []
		for i in xrange(0, self.threadCount):
			self.statusText.append(wx.StaticText(self, -1, _("Building: %d                           ") % (len(self.sliceCmdList))))
			self.progressGauge.append(wx.Gauge(self, -1))
			self.progressGauge[i].SetRange(10000)
		self.progressTextTotal = wx.StaticText(self, -1, _("Done: 0/%d                           ") % (len(self.sliceCmdList)))
		self.progressGaugeTotal = wx.Gauge(self, -1)
		self.progressGaugeTotal.SetRange(len(self.sliceCmdList))
		self.abortButton = wx.Button(self, -1, _("Abort"))
		for i in xrange(0, self.threadCount):
			self.sizer.Add(self.statusText[i], (i*2,0), span=(1,4))
			self.sizer.Add(self.progressGauge[i], (1+i*2, 0), span=(1,4), flag=wx.EXPAND)
		self.sizer.Add(self.progressTextTotal, (self.threadCount*2,0), span=(1,4))
		self.sizer.Add(self.progressGaugeTotal, (1+self.threadCount*2, 0), span=(1,4), flag=wx.EXPAND)

		self.sizer.Add(self.abortButton, (2+self.threadCount*2,0), span=(1,4), flag=wx.ALIGN_CENTER)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableRow(0)

		self.Bind(wx.EVT_BUTTON, self.OnAbort, self.abortButton)
		self.SetSizer(self.sizer)
		self.Layout()
		self.Fit()
		
		threading.Thread(target=self.OnRunManager).start()

	def OnAbort(self, e):
		if self.abort:
			self.Close()
		else:
			self.abort = True
			self.abortButton.SetLabel(_("Close"))

	def SetProgress(self, index, stepName, layer, maxLayer):
		if self.prevStep[index] != stepName:
			self.totalDoneFactor[index] += sliceRun.sliceStepTimeFactor[self.prevStep[index]]
			newTime = time.time()
			self.prevStep[index] = stepName
		
		progresValue = ((self.totalDoneFactor[index] + sliceRun.sliceStepTimeFactor[stepName] * layer / maxLayer) / sliceRun.totalRunTimeFactor) * 10000
		self.progressGauge[index].SetValue(int(progresValue))
		self.statusText[index].SetLabel(stepName + " [" + str(layer) + "/" + str(maxLayer) + "]")
	
	def OnRunManager(self):
		threads = []
		for i in xrange(0, self.threadCount):
			threads.append(threading.Thread(target=self.OnRun, args=(i,)))

		for t in threads:
			t.start()
		for t in threads:
			t.join()

		self.abort = True
		sliceTime = time.time() - self.sliceStartTime
		status = _("Build: %d models") % (len(self.sliceCmdList))
		status += _("\nSlicing took: %(hours)02d:%(minutes)02d") % (sliceTime / 60, sliceTime % 60)

		wx.CallAfter(self.statusText[0].SetLabel, status)
		wx.CallAfter(self.OnSliceDone)
	
	def OnRun(self, index):
		while self.cmdIndex < len(self.sliceCmdList):
			cmdIndex = self.cmdIndex;
			self.cmdIndex += 1			
			action = self.sliceCmdList[cmdIndex]
			wx.CallAfter(self.SetTitle, _("Building: [%(index)d/%(size)d]")  % (self.sliceCmdList.index(action) + 1, len(self.sliceCmdList)))

			p = sliceRun.startSliceCommandProcess(action)
			line = p.stdout.readline()
			maxValue = 1
			while(len(line) > 0):
				line = line.rstrip()
				if line[0:9] == "Progress[" and line[-1:] == "]":
					progress = line[9:-1].split(":")
					if len(progress) > 2:
						maxValue = int(progress[2])
					wx.CallAfter(self.SetProgress, index, progress[0], int(progress[1]), maxValue)
				else:
					wx.CallAfter(self.statusText[index].SetLabel, line)
				if self.abort:
					p.terminate()
					wx.CallAfter(self.statusText[index].SetLabel, _("Aborted by user."))
					return
				line = p.stdout.readline()
			self.returnCode = p.wait()

			# Update output gocde file...
			# Warning: the user could have changed the profile between the slcer run and this code.  We might be using old information.
			gcodeFilename = self.outputFilenameList[index]
			gcode = gcodeInterpreter.gcode()
			gcode.load(gcodeFilename)
			profile.replaceGCodeTags(gcodeFilename, gcode)
			
			wx.CallAfter(self.progressGauge[index].SetValue, 10000)
			self.totalDoneFactor[index] = 0.0
			wx.CallAfter(self.progressTextTotal.SetLabel, _("Done %(index)d/%(size)d") % (self.cmdIndex, len(self.sliceCmdList)))
			wx.CallAfter(self.progressGaugeTotal.SetValue, self.cmdIndex)
	
	def OnSliceDone(self):
		self.abortButton.Destroy()
		self.closeButton = wx.Button(self, -1, _("Close"))
		self.sizer.Add(self.closeButton, (2+self.threadCount*2,0), span=(1,1))
		if profile.getPreference('sdpath') != '':
			self.copyToSDButton = wx.Button(self, -1, _("To SDCard"))
			self.Bind(wx.EVT_BUTTON, self.OnCopyToSD, self.copyToSDButton)
			self.sizer.Add(self.copyToSDButton, (2+self.threadCount*2,1), span=(1,1))
		self.Bind(wx.EVT_BUTTON, self.OnAbort, self.closeButton)
		self.Layout()
		self.Fit()

	def OnCopyToSD(self, e):
		for f in self.filenameList:
			exportFilename = sliceRun.getExportFilename(f)
			filename = os.path.basename(exportFilename)
			if profile.getPreference('sdshortnames') == 'True':
				filename = sliceRun.getShortFilename(filename)
			shutil.copy(exportFilename, os.path.join(profile.getPreference('sdpath'), filename))
