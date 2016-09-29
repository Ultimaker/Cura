__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import webbrowser
import threading
import time
import math

import wx
import wx.wizard

from Cura.gui import firmwareInstall
from Cura.gui import printWindow
from Cura.util import machineCom
from Cura.util import profile
from Cura.util import gcodeGenerator
from Cura.util import resources
from Cura.util import version


class InfoBox(wx.Panel):
	def __init__(self, parent):
		super(InfoBox, self).__init__(parent)
		self.SetBackgroundColour('#FFFF80')

		self.sizer = wx.GridBagSizer(5, 5)
		self.SetSizer(self.sizer)

		self.attentionBitmap = wx.Bitmap(resources.getPathForImage('attention.png'))
		self.errorBitmap = wx.Bitmap(resources.getPathForImage('error.png'))
		self.readyBitmap = wx.Bitmap(resources.getPathForImage('ready.png'))
		self.busyBitmap = [
			wx.Bitmap(resources.getPathForImage('busy-0.png')),
			wx.Bitmap(resources.getPathForImage('busy-1.png')),
			wx.Bitmap(resources.getPathForImage('busy-2.png')),
			wx.Bitmap(resources.getPathForImage('busy-3.png'))
		]

		self.bitmap = wx.StaticBitmap(self, -1, wx.EmptyBitmapRGBA(24, 24, red=255, green=255, blue=255, alpha=1))
		self.text = wx.StaticText(self, -1, '')
		self.extraInfoButton = wx.Button(self, -1, 'i', style=wx.BU_EXACTFIT)
		self.sizer.Add(self.bitmap, pos=(0, 0), flag=wx.ALL, border=5)
		self.sizer.Add(self.text, pos=(0, 1), flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.Add(self.extraInfoButton, pos=(0,2), flag=wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, border=5)
		self.sizer.AddGrowableCol(1)

		self.extraInfoButton.Show(False)

		self.extraInfoUrl = ''
		self.busyState = None
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.doBusyUpdate, self.timer)
		self.Bind(wx.EVT_BUTTON, self.doExtraInfo, self.extraInfoButton)
		self.timer.Start(100)

	def SetInfo(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.Refresh()

	def SetError(self, info, extraInfoUrl):
		self.extraInfoUrl = extraInfoUrl
		self.SetBackgroundColour('#FF8080')
		self.text.SetLabel(info)
		if extraInfoUrl:
			self.extraInfoButton.Show(True)
		self.Layout()
		self.SetErrorIndicator()
		self.Refresh()

	def SetAttention(self, info):
		self.SetBackgroundColour('#FFFF80')
		self.text.SetLabel(info)
		self.extraInfoButton.Show(False)
		self.SetAttentionIndicator()
		self.Layout()
		self.Refresh()

	def SetBusy(self, info):
		self.SetInfo(info)
		self.SetBusyIndicator()

	def SetBusyIndicator(self):
		self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def doExtraInfo(self, e):
		webbrowser.open(self.extraInfoUrl)

	def doBusyUpdate(self, e):
		if self.busyState is None:
			return
		self.busyState += 1
		if self.busyState >= len(self.busyBitmap):
			self.busyState = 0
		self.bitmap.SetBitmap(self.busyBitmap[self.busyState])

	def SetReadyIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.readyBitmap)

	def SetErrorIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.errorBitmap)

	def SetAttentionIndicator(self):
		self.busyState = None
		self.bitmap.SetBitmap(self.attentionBitmap)

class ImageButton(wx.Panel):
	DefaultOverlay = wx.Bitmap(resources.getPathForImage('ImageButton_Overlay.png'))
	IB_GROUP=1
	__groups__ = {}
	__last_group__ = None
	def __init__(self, parent, label, bitmap, extra_label=None, overlay=DefaultOverlay, style=None):
		super(ImageButton, self).__init__(parent)

		if style is ImageButton.IB_GROUP:
			ImageButton.__last_group__ = self
			ImageButton.__groups__[self] = [self]
			self.group = self
		else:
			if ImageButton.__last_group__:
				ImageButton.__groups__[ImageButton.__last_group__].append(self)
				self.group = ImageButton.__last_group__
			else:
				self.group = None
		self.sizer = wx.StaticBoxSizer(wx.StaticBox(self), wx.VERTICAL)
		self.SetSizer(self.sizer)
		self.bitmap = bitmap
		self.original_overlay = overlay
		self.overlay = self.createOverlay(bitmap, overlay)
		self.text = wx.StaticText(self, -1, label)
		self.bmp = wx.StaticBitmap(self, -1, self.bitmap)
		if extra_label:
			self.extra_text = wx.StaticText(self, -1, extra_label)
		else:
			self.extra_text = None
		self.selected = False
		self.callback = None

		self.sizer.Add(self.text, 0, flag=wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, border=5)
		self.sizer.Add(self.bmp, 1, flag=wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, border=5)
		if self.extra_text:
			self.sizer.Add(self.extra_text, 0, flag=wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, border=5)
		self.bmp.Bind(wx.EVT_LEFT_UP, self.OnLeftClick)

	def __del__(self):
		if self.group:
			ImageButton.__groups__[self.group].remove(self)
			if self == self.group:
				for ib in ImageButton.__groups__[self.group]:
					ib.group = None
				del ImageButton.__groups__[self.group]
				if ImageButton.__last_group__ == self:
					ImageButton.__last_group__ = None

	def TriggerGroupCallbacks(self):
		if self.group:
			for ib in ImageButton.__groups__[self.group]:
				if ib.GetValue() and ib.callback:
					ib.callback()
					break
		else:
			if self.GetValue() and self.callback:
				self.callback()

	def OnLeftClick(self, e):
		self.SetValue(True)

	def GetValue(self):
		return self.selected

	def SetValue(self, value):
		old_value = self.selected
		self.selected = bool(value)
		self.bmp.SetBitmap(self.overlay if self.GetValue() else self.bitmap)
		if self.selected and self.group:
			for ib in ImageButton.__groups__[self.group]:
				if ib == self:
					continue
				ib.SetValue(False)
		self.Layout()
		if self.callback and not old_value and self.selected:
			self.callback()

	def SetLabel(self, label):
		self.text.SetLabel(label)
		self.Layout()

	def SetExtraLabel(self, label):
		if self.extra_text:
			self.extra_text.SetLabel(label)
		else:
			self.extra_text = wx.StaticText(self, -1, label)
			self.sizer.Add(self.extra_text, 0, flag=wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, border=5)
		self.Layout()

	def SetBitmap(self, bitmap):
		self.bitmap = bitmap
		self.overlay = self.createOverlay(bitmap, self.original_overlay)
		self.bmp.SetBitmap(self.overlay if self.GetValue() else self.bitmap)
		self.Layout()

	def SetOverlay(self, overlay):
		self.original_overlay = overlay
		self.overlay = self.createOverlay(self.bitmap, self.original_overlay)
		self.bmp.SetBitmap(self.overlay if self.GetValue() else self.bitmap)
		self.Layout()

	def OnSelected(self, callback):
		self.callback = callback

	def createOverlay(self, bitmap, overlay):
		result = bitmap.GetSubBitmap(wx.Rect(0, 0, *bitmap.Size))
		(width, height) = bitmap.GetSize()
		overlay_image = wx.ImageFromBitmap(overlay)
		overlay_image = overlay_image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
		overlay_scaled = wx.BitmapFromImage(overlay_image)
		dc = wx.MemoryDC()
		dc.SelectObject(result)
		dc.DrawBitmap(overlay_scaled, 0, 0)
		dc.SelectObject(wx.NullBitmap)
		return result


class InfoPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent, title):
		wx.wizard.WizardPageSimple.__init__(self, parent)

		parent.GetPageAreaSizer().Add(self)
		sizer = wx.GridBagSizer(5, 5)
		self.sizer = sizer
		self.SetSizer(sizer)

		self.title = wx.StaticText(self, -1, title)
		font = wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD)
		self.title.SetFont(font)
		# HACK ALERT: For some reason, the StaticText keeps its same size as if
		# the font was not modified, this causes the text to wrap and to
		# get out of bounds of the widgets area and hide other widgets.
		# The only way I found for the widget to get its right size was to calculate
		# the new font's extent and set the min size on the widget
		self.title.SetMinSize(self.GetTextExtent(font, title))
		sizer.Add(self.title, pos=(0, 0), span=(1, 2), flag=wx.ALIGN_CENTRE | wx.ALL)
		sizer.Add(wx.StaticLine(self, -1), pos=(1, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		sizer.AddGrowableCol(1)

		self.rowNr = 2

	def GetTextExtent(self, font, text):
		dc = wx.ScreenDC()
		dc.SetFont(font)
		w,h = dc.GetTextExtent(text)
		return (w, h)

	def AddText(self, info):
		text = wx.StaticText(self, -1, info)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return text

	def AddTextUrl(self, info, link, url):
		text = wx.StaticText(self, -1, info)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		text2 = wx.StaticText(self, -1, link)
		text2.SetForegroundColour(wx.BLUE)
		def url_clicked(e):
			webbrowser.open(url)
		text2.Bind(wx.EVT_LEFT_DOWN, url_clicked)
		self.GetSizer().Add(text2, pos=(self.rowNr, 1), span=(1, 1), border=0)
		self.rowNr += 1
		return text

	def AddSeperator(self):
		self.GetSizer().Add(wx.StaticLine(self, -1), pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1

	def AddHiddenSeperator(self):
		self.AddText("")

	def AddInfoBox(self):
		infoBox = InfoBox(self)
		self.GetSizer().Add(infoBox, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
		self.rowNr += 1
		return infoBox

	def AddRadioButton(self, label, style=0):
		radio = wx.RadioButton(self, -1, label, style=style)
		self.GetSizer().Add(radio, pos=(self.rowNr, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
		self.rowNr += 1
		return radio

	def AddCheckbox(self, label, checked=False):
		check = wx.CheckBox(self, -1)
		text = wx.StaticText(self, -1, label)
		check.SetValue(checked)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 2), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AddButton(self, label):
		button = wx.Button(self, -1, label)
		self.GetSizer().Add(button, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return button

	def AddDualButton(self, label1, label2):
		button1 = wx.Button(self, -1, label1)
		self.GetSizer().Add(button1, pos=(self.rowNr, 0), flag=wx.RIGHT)
		button2 = wx.Button(self, -1, label2)
		self.GetSizer().Add(button2, pos=(self.rowNr, 1))
		self.rowNr += 1
		return button1, button2

	def AddTextCtrl(self, value):
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(ret, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddLabelTextCtrl(self, info, value):
		text = wx.StaticText(self, -1, info)
		ret = wx.TextCtrl(self, -1, value)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(ret, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return ret

	def AddTextCtrlButton(self, value, buttonText):
		text = wx.TextCtrl(self, -1, value)
		button = wx.Button(self, -1, buttonText)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT)
		self.GetSizer().Add(button, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT)
		self.rowNr += 1
		return text, button

	def AddBitmap(self, bitmap):
		bitmap = wx.StaticBitmap(self, -1, bitmap)
		self.GetSizer().Add(bitmap, pos=(self.rowNr, 0), span=(1, 2), flag=wx.LEFT | wx.RIGHT)
		self.rowNr += 1
		return bitmap

	def AddPanel(self):
		panel = wx.Panel(self, -1)
		sizer = wx.GridBagSizer(2, 2)
		panel.SetSizer(sizer)
		self.GetSizer().Add(panel, pos=(self.rowNr, 0), span=(1, 2), flag=wx.ALL | wx.EXPAND)
		self.rowNr += 1
		return panel

	def AddCheckmark(self, label, bitmap):
		check = wx.StaticBitmap(self, -1, bitmap)
		text = wx.StaticText(self, -1, label)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT)
		self.GetSizer().Add(check, pos=(self.rowNr, 1), span=(1, 1), flag=wx.ALL)
		self.rowNr += 1
		return check

	def AddCombo(self, label, options):
		combo = wx.ComboBox(self, -1, options[0], choices=options, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		text = wx.StaticText(self, -1, label)
		self.GetSizer().Add(text, pos=(self.rowNr, 0), span=(1, 1), flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER)
		self.GetSizer().Add(combo, pos=(self.rowNr, 1), span=(1, 1), flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
		self.rowNr += 1
		return combo

	def AddImageButton(self, panel, x, y, label, filename, image_size=None,
					   extra_label=None, overlay=ImageButton.DefaultOverlay, style=None):
		ib = ImageButton(panel, label, self.GetBitmap(filename, image_size), extra_label, overlay, style)
		panel.GetSizer().Add(ib, pos=(x, y), flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
		return ib

	def GetBitmap(self, filename, image_size):
		if image_size == None:
			return wx.Bitmap(resources.getPathForImage(filename))
		else:
			image = wx.Image(resources.getPathForImage(filename))
			image_scaled = image.Scale(image_size[0], image_size[1], wx.IMAGE_QUALITY_HIGH)
			return wx.BitmapFromImage(image_scaled)

	def AllowNext(self):
		return True

	def AllowBack(self):
		return True

	def StoreData(self):
		pass

class PrintrbotPage(InfoPage):
	def __init__(self, parent):
		self._printer_info = [
			# X, Y, Z, Nozzle Size, Filament Diameter, PrintTemperature, Print Speed, Travel Speed, Retract speed, Retract amount, use bed level sensor
			("Simple Metal", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			("Metal Plus", 250, 250, 250, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			("Simple Makers Kit", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			(":" + _("Older models"),),
			("Original", 130, 130, 130, 0.5, 2.95, 208, 40, 70, 30, 1, False),
			("Simple Maker's Edition v1", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Simple Maker's Edition v2 (2013 Printrbot Simple)", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Simple Maker's Edition v3 (2014 Printrbot Simple)", 100, 100, 100, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Jr v1", 115, 120, 80, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Jr v2", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("LC v1", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("LC v2", 150, 150, 150, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v1", 200, 200, 200, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v2", 200, 200, 200, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v2.1", 185, 220, 200, 0.4, 1.75, 208, 40, 70, 30, 1, False),
			("Plus v2.2 (Model 1404/140422/140501/140507)", 250, 250, 250, 0.4, 1.75, 208, 40, 70, 30, 1, True),
			("Go v2 Large", 505, 306, 310, 0.4, 1.75, 208, 35, 70, 30, 1, True),
		]

		super(PrintrbotPage, self).__init__(parent, _("Printrbot Selection"))
		self.AddBitmap(wx.Bitmap(resources.getPathForImage('Printrbot_logo.png')))
		self.AddText(_("Select which Printrbot machine you have:"))
		self._items = []
		for printer in self._printer_info:
			if printer[0].startswith(":"):
				self.AddSeperator()
				self.AddText(printer[0][1:])
			else:
				item = self.AddRadioButton(printer[0])
				item.data = printer[1:]
				self._items.append(item)

	def StoreData(self):
		profile.putMachineSetting('machine_name', 'Printrbot ???')
		for item in self._items:
			if item.GetValue():
				data = item.data
				profile.putMachineSetting('machine_name', 'Printrbot ' + item.GetLabel())
				profile.putMachineSetting('machine_width', data[0])
				profile.putMachineSetting('machine_depth', data[1])
				profile.putMachineSetting('machine_height', data[2])
				profile.putProfileSetting('nozzle_size', data[3])
				profile.putProfileSetting('filament_diameter', data[4])
				profile.putProfileSetting('print_temperature', data[5])
				profile.putProfileSetting('print_speed', data[6])
				profile.putProfileSetting('travel_speed', data[7])
				profile.putProfileSetting('retraction_speed', data[8])
				profile.putProfileSetting('retraction_amount', data[9])
				profile.putProfileSetting('wall_thickness', float(profile.getProfileSettingFloat('nozzle_size')) * 2)
				profile.putMachineSetting('has_heated_bed', 'False')
				profile.putMachineSetting('machine_center_is_zero', 'False')
				profile.putMachineSetting('extruder_head_size_min_x', '0')
				profile.putMachineSetting('extruder_head_size_min_y', '0')
				profile.putMachineSetting('extruder_head_size_max_x', '0')
				profile.putMachineSetting('extruder_head_size_max_y', '0')
				profile.putMachineSetting('extruder_head_size_height', '0')
				if data[10]:
					profile.setAlterationFile('start.gcode', """;Sliced at: {day} {date} {time}
;Basic settings: Layer height: {layer_height} Walls: {wall_thickness} Fill: {fill_density}
;Print time: {print_time}
;Filament used: {filament_amount}m {filament_weight}g
;Filament cost: {filament_cost}
;M190 S{print_bed_temperature} ;Uncomment to add your own bed temperature line
;M109 S{print_temperature} ;Uncomment to add your own temperature line
G21        ;metric values
G90        ;absolute positioning
M82        ;set extruder to absolute mode
M107       ;start with the fan off
G28 X0 Y0  ;move X/Y to min endstops
G28 Z0     ;move Z to min endstops
G29        ;Run the auto bed leveling
G1 Z15.0 F{travel_speed} ;move the platform down 15mm
G92 E0                  ;zero the extruded length
G1 F200 E3              ;extrude 3mm of feed stock
G92 E0                  ;zero the extruded length again
G1 F{travel_speed}
;Put printing message on LCD screen
M117 Printing...
""")

class OtherMachineSelectPage(InfoPage):
	def __init__(self, parent):
		super(OtherMachineSelectPage, self).__init__(parent, _("Other machine information"))
		self.AddText(_("The following pre-defined machine profiles are available"))
		self.AddText(_("Note that these profiles are not guaranteed to give good results,\nor work at all. Extra tweaks might be required.\nIf you find issues with the predefined profiles,\nor want an extra profile.\nPlease report it at the github issue tracker."))
		self.options = []
		machines = resources.getDefaultMachineProfiles()
		machines.sort()
		for filename in machines:
			name = os.path.splitext(os.path.basename(filename))[0]
			item = self.AddRadioButton(name)
			item.filename = filename
			item.Bind(wx.EVT_RADIOBUTTON, self.OnProfileSelect)
			self.options.append(item)
		self.AddSeperator()
		item = self.AddRadioButton(_('Custom...'))
		item.SetValue(True)
		item.Bind(wx.EVT_RADIOBUTTON, self.OnOtherSelect)

	def OnProfileSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().otherMachineInfoPage)

	def OnOtherSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().customRepRapInfoPage)

	def StoreData(self):
		for option in self.options:
			if option.GetValue():
				profile.loadProfile(option.filename)
				profile.loadMachineSettings(option.filename)

class OtherMachineInfoPage(InfoPage):
	def __init__(self, parent):
		super(OtherMachineInfoPage, self).__init__(parent, _("Cura Ready!"))
		self.AddText(_("Cura is now ready to be used!"))

class CustomRepRapInfoPage(InfoPage):
	def __init__(self, parent):
		super(CustomRepRapInfoPage, self).__init__(parent, _("Custom RepRap information"))
		self.AddText(_("RepRap machines can be vastly different, so here you can set your own settings."))
		self.AddText(_("Be sure to review the default profile before running it on your machine."))
		self.AddText(_("If you like a default profile for your machine added,\nthen make an issue on github."))
		self.AddSeperator()
		self.AddText(_("You will have to manually install Marlin or Sprinter firmware."))
		self.AddSeperator()
		self.machineName = self.AddLabelTextCtrl(_("Machine name"), "RepRap")
		self.machineWidth = self.AddLabelTextCtrl(_("Machine width X (mm)"), "80")
		self.machineDepth = self.AddLabelTextCtrl(_("Machine depth Y (mm)"), "80")
		self.machineHeight = self.AddLabelTextCtrl(_("Machine height Z (mm)"), "55")
		self.nozzleSize = self.AddLabelTextCtrl(_("Nozzle size (mm)"), "0.5")
		self.heatedBed = self.AddCheckbox(_("Heated bed"))
		self.HomeAtCenter = self.AddCheckbox(_("Bed center is 0,0,0 (RoStock)"))

	def StoreData(self):
		profile.putMachineSetting('machine_name', self.machineName.GetValue())
		profile.putMachineSetting('machine_width', self.machineWidth.GetValue())
		profile.putMachineSetting('machine_depth', self.machineDepth.GetValue())
		profile.putMachineSetting('machine_height', self.machineHeight.GetValue())
		profile.putProfileSetting('nozzle_size', self.nozzleSize.GetValue())
		profile.putProfileSetting('wall_thickness', float(profile.getProfileSettingFloat('nozzle_size')) * 2)
		profile.putMachineSetting('has_heated_bed', str(self.heatedBed.GetValue()))
		profile.putMachineSetting('machine_center_is_zero', str(self.HomeAtCenter.GetValue()))
		profile.putMachineSetting('extruder_head_size_min_x', '0')
		profile.putMachineSetting('extruder_head_size_min_y', '0')
		profile.putMachineSetting('extruder_head_size_max_x', '0')
		profile.putMachineSetting('extruder_head_size_max_y', '0')
		profile.putMachineSetting('extruder_head_size_height', '0')
		profile.checkAndUpdateMachineName()

class MachineSelectPage(InfoPage):
	def __init__(self, parent):
		super(MachineSelectPage, self).__init__(parent, _("Select your machine"))
		self.AddText(_("What kind of machine do you have:"))

		self.Ultimaker2Radio = self.AddRadioButton("Ultimaker2")
		self.Ultimaker2Radio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		self.Ultimaker2ExtRadio = self.AddRadioButton("Ultimaker2extended")
		self.Ultimaker2ExtRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		self.Ultimaker2GoRadio = self.AddRadioButton("Ultimaker2go")
		self.Ultimaker2GoRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimaker2Select)
		self.UltimakerRadio = self.AddRadioButton("Ultimaker Original")
		self.UltimakerRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimakerSelect)
		self.UltimakerOPRadio = self.AddRadioButton("Ultimaker Original+")
		self.UltimakerOPRadio.Bind(wx.EVT_RADIOBUTTON, self.OnUltimakerOPSelect)
		self.PrintrbotRadio = self.AddRadioButton("Printrbot")
		self.PrintrbotRadio.Bind(wx.EVT_RADIOBUTTON, self.OnPrintrbotSelect)
		self.OtherRadio = self.AddRadioButton(_("Other (Ex: RepRap, MakerBot, Witbox)"))
		self.OtherRadio.Bind(wx.EVT_RADIOBUTTON, self.OnOtherSelect)

	def OnUltimaker2Select(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().ultimaker2ReadyPage)

	def OnUltimakerSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().ultimakerSelectParts)

	def OnUltimakerOPSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().ultimakerFirmwareUpgradePage)

	def OnPrintrbotSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().printrbotSelectType)

	def OnOtherSelect(self, e):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().otherMachineSelectPage)

	def StoreData(self):
		profile.putProfileSetting('retraction_enable', 'True')
		if self.Ultimaker2Radio.GetValue() or self.Ultimaker2GoRadio.GetValue() or self.Ultimaker2ExtRadio.GetValue():
			if self.Ultimaker2Radio.GetValue():
				profile.putMachineSetting('machine_width', '230')
				profile.putMachineSetting('machine_depth', '225')
				profile.putMachineSetting('machine_height', '205')
				profile.putMachineSetting('machine_name', 'ultimaker2')
				profile.putMachineSetting('machine_type', 'ultimaker2')
				profile.putMachineSetting('has_heated_bed', 'True')
			if self.Ultimaker2GoRadio.GetValue():
				profile.putMachineSetting('machine_width', '120')
				profile.putMachineSetting('machine_depth', '120')
				profile.putMachineSetting('machine_height', '115')
				profile.putMachineSetting('machine_name', 'ultimaker2go')
				profile.putMachineSetting('machine_type', 'ultimaker2go')
				profile.putMachineSetting('has_heated_bed', 'False')
			if self.Ultimaker2ExtRadio.GetValue():
				profile.putMachineSetting('machine_width', '230')
				profile.putMachineSetting('machine_depth', '225')
				profile.putMachineSetting('machine_height', '315')
				profile.putMachineSetting('machine_name', 'ultimaker2extended')
				profile.putMachineSetting('machine_type', 'ultimaker2extended')
				profile.putMachineSetting('has_heated_bed', 'False')
			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'UltiGCode')
			profile.putMachineSetting('extruder_head_size_min_x', '40.0')
			profile.putMachineSetting('extruder_head_size_min_y', '10.0')
			profile.putMachineSetting('extruder_head_size_max_x', '60.0')
			profile.putMachineSetting('extruder_head_size_max_y', '30.0')
			profile.putMachineSetting('extruder_head_size_height', '48.0')
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putProfileSetting('fan_full_height', '5.0')
			profile.putMachineSetting('extruder_offset_x1', '18.0')
			profile.putMachineSetting('extruder_offset_y1', '0.0')
		elif self.UltimakerRadio.GetValue():
			profile.putMachineSetting('machine_width', '205')
			profile.putMachineSetting('machine_depth', '205')
			profile.putMachineSetting('machine_height', '200')
			profile.putMachineSetting('machine_name', 'ultimaker original')
			profile.putMachineSetting('machine_type', 'ultimaker')
			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putMachineSetting('extruder_head_size_min_x', '75.0')
			profile.putMachineSetting('extruder_head_size_min_y', '18.0')
			profile.putMachineSetting('extruder_head_size_max_x', '18.0')
			profile.putMachineSetting('extruder_head_size_max_y', '35.0')
			profile.putMachineSetting('extruder_head_size_height', '55.0')
		elif self.UltimakerOPRadio.GetValue():
			profile.putMachineSetting('machine_width', '205')
			profile.putMachineSetting('machine_depth', '205')
			profile.putMachineSetting('machine_height', '200')
			profile.putMachineSetting('machine_name', 'ultimaker original+')
			profile.putMachineSetting('machine_type', 'ultimaker_plus')
			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putProfileSetting('nozzle_size', '0.4')
			profile.putMachineSetting('extruder_head_size_min_x', '75.0')
			profile.putMachineSetting('extruder_head_size_min_y', '18.0')
			profile.putMachineSetting('extruder_head_size_max_x', '18.0')
			profile.putMachineSetting('extruder_head_size_max_y', '35.0')
			profile.putMachineSetting('extruder_head_size_height', '55.0')
			profile.putMachineSetting('has_heated_bed', 'True')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putProfileSetting('retraction_enable', 'True')
		else:
			profile.putMachineSetting('machine_width', '80')
			profile.putMachineSetting('machine_depth', '80')
			profile.putMachineSetting('machine_height', '60')
			profile.putMachineSetting('machine_name', 'reprap')
			profile.putMachineSetting('machine_type', 'reprap')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putPreference('startMode', 'Normal')
			profile.putProfileSetting('nozzle_size', '0.5')
		profile.checkAndUpdateMachineName()
		profile.putProfileSetting('wall_thickness', float(profile.getProfileSetting('nozzle_size')) * 2)

class SelectParts(InfoPage):
	def __init__(self, parent):
		super(SelectParts, self).__init__(parent, _("Select upgraded parts you have"))
		self.AddText(_("To assist you in having better default settings for your Ultimaker\nCura would like to know which upgrades you have in your machine."))
		self.AddSeperator()
		self.springExtruder = self.AddCheckbox(_("Extruder drive upgrade"))
		self.heatedBedKit = self.AddCheckbox(_("Heated printer bed (kit)"))
		self.heatedBed = self.AddCheckbox(_("Heated printer bed (self built)"))
		self.dualExtrusion = self.AddCheckbox(_("Dual extrusion (experimental)"))
		self.AddSeperator()
		self.AddText(_("If you have an Ultimaker bought after october 2012 you will have the\nExtruder drive upgrade. If you do not have this upgrade,\nit is highly recommended to improve reliability."))
		self.AddText(_("This upgrade can be bought from the Ultimaker webshop\nor found on thingiverse as thing:26094"))
		self.springExtruder.SetValue(True)

	def StoreData(self):
		profile.putMachineSetting('ultimaker_extruder_upgrade', str(self.springExtruder.GetValue()))
		if self.heatedBed.GetValue() or self.heatedBedKit.GetValue():
			profile.putMachineSetting('has_heated_bed', 'True')
		else:
			profile.putMachineSetting('has_heated_bed', 'False')
		if self.dualExtrusion.GetValue():
			profile.putMachineSetting('extruder_amount', '2')
			profile.putMachineSetting('machine_depth', '195')
		else:
			profile.putMachineSetting('extruder_amount', '1')
		if profile.getMachineSetting('ultimaker_extruder_upgrade') == 'True':
			profile.putProfileSetting('retraction_enable', 'True')
		else:
			profile.putProfileSetting('retraction_enable', 'False')


class UltimakerFirmwareUpgradePage(InfoPage):
	def __init__(self, parent):
		super(UltimakerFirmwareUpgradePage, self).__init__(parent, _("Upgrade Ultimaker Firmware"))
		self.AddText(_("Firmware is the piece of software running directly on your 3D printer.\nThis firmware controls the stepper motors, regulates the temperature\nand ultimately makes your printer work."))
		self.AddHiddenSeperator()
		self.AddText(_("The firmware shipping with new Ultimakers works, but upgrades\nhave been made to make better prints, and make calibration easier."))
		self.AddHiddenSeperator()
		self.AddText(_("Cura requires these new features and thus\nyour firmware will most likely need to be upgraded.\nYou will get the chance to do so now."))
		upgradeButton, skipUpgradeButton = self.AddDualButton(_('Upgrade to Marlin firmware'), _('Skip upgrade'))
		upgradeButton.Bind(wx.EVT_BUTTON, self.OnUpgradeClick)
		skipUpgradeButton.Bind(wx.EVT_BUTTON, self.OnSkipClick)
		self.AddHiddenSeperator()
		if profile.getMachineSetting('machine_type') == 'ultimaker':
			self.AddText(_("Do not upgrade to this firmware if:"))
			self.AddText(_("* You have an older machine based on ATMega1280 (Rev 1 machine)"))
			self.AddText(_("* Build your own heated bed"))
			self.AddText(_("* Have other changes in the firmware"))
#		button = self.AddButton('Goto this page for a custom firmware')
#		button.Bind(wx.EVT_BUTTON, self.OnUrlClick)

	def AllowNext(self):
		return False

	def OnUpgradeClick(self, e):
		if firmwareInstall.InstallFirmware():
			self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()

	def OnSkipClick(self, e):
		self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()
		self.GetParent().ShowPage(self.GetNext())

	def OnUrlClick(self, e):
		webbrowser.open('http://marlinbuilder.robotfuzz.com/')

class UltimakerCheckupPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCheckupPage, self).__init__(parent, _("Ultimaker Checkup"))

		self.checkBitmap = wx.Bitmap(resources.getPathForImage('checkmark.png'))
		self.crossBitmap = wx.Bitmap(resources.getPathForImage('cross.png'))
		self.unknownBitmap = wx.Bitmap(resources.getPathForImage('question.png'))
		self.endStopNoneBitmap = wx.Bitmap(resources.getPathForImage('endstop_none.png'))
		self.endStopXMinBitmap = wx.Bitmap(resources.getPathForImage('endstop_xmin.png'))
		self.endStopXMaxBitmap = wx.Bitmap(resources.getPathForImage('endstop_xmax.png'))
		self.endStopYMinBitmap = wx.Bitmap(resources.getPathForImage('endstop_ymin.png'))
		self.endStopYMaxBitmap = wx.Bitmap(resources.getPathForImage('endstop_ymax.png'))
		self.endStopZMinBitmap = wx.Bitmap(resources.getPathForImage('endstop_zmin.png'))
		self.endStopZMaxBitmap = wx.Bitmap(resources.getPathForImage('endstop_zmax.png'))

		self.AddText(
			_("It is a good idea to do a few sanity checks now on your Ultimaker.\nYou can skip these if you know your machine is functional."))
		b1, b2 = self.AddDualButton(_("Run checks"), _("Skip checks"))
		b1.Bind(wx.EVT_BUTTON, self.OnCheckClick)
		b2.Bind(wx.EVT_BUTTON, self.OnSkipClick)
		self.AddSeperator()
		self.commState = self.AddCheckmark(_("Communication:"), self.unknownBitmap)
		self.tempState = self.AddCheckmark(_("Temperature:"), self.unknownBitmap)
		self.stopState = self.AddCheckmark(_("Endstops:"), self.unknownBitmap)
		self.AddSeperator()
		self.infoBox = self.AddInfoBox()
		self.machineState = self.AddText("")
		self.temperatureLabel = self.AddText("")
		self.errorLogButton = self.AddButton(_("Show error log"))
		self.errorLogButton.Show(False)
		self.AddSeperator()
		self.endstopBitmap = self.AddBitmap(self.endStopNoneBitmap)
		self.comm = None
		self.xMinStop = False
		self.xMaxStop = False
		self.yMinStop = False
		self.yMaxStop = False
		self.zMinStop = False
		self.zMaxStop = False

		self.Bind(wx.EVT_BUTTON, self.OnErrorLog, self.errorLogButton)

	def __del__(self):
		if self.comm is not None:
			self.comm.close()

	def AllowNext(self):
		self.endstopBitmap.Show(False)
		return False

	def OnSkipClick(self, e):
		self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()
		self.GetParent().ShowPage(self.GetNext())

	def OnCheckClick(self, e=None):
		self.errorLogButton.Show(False)
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnCheckClick)
			return
		self.infoBox.SetBusy(_("Connecting to machine."))
		self.commState.SetBitmap(self.unknownBitmap)
		self.tempState.SetBitmap(self.unknownBitmap)
		self.stopState.SetBitmap(self.unknownBitmap)
		self.checkupState = 0
		self.checkExtruderNr = 0
		self.comm = machineCom.MachineCom(callbackObject=self)

	def OnErrorLog(self, e):
		printWindow.LogWindow('\n'.join(self.comm.getLog()))

	def mcLog(self, message):
		pass

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if not self.comm.isOperational():
			return
		if self.checkupState == 0:
			self.tempCheckTimeout = 20
			if temp[self.checkExtruderNr] > 70:
				self.checkupState = 1
				wx.CallAfter(self.infoBox.SetInfo, _("Cooldown before temperature check."))
				self.comm.sendCommand("M104 S0 T%d" % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
			else:
				self.startTemp = temp[self.checkExtruderNr]
				self.checkupState = 2
				wx.CallAfter(self.infoBox.SetInfo, _("Checking the heater and temperature sensor."))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
		elif self.checkupState == 1:
			if temp[self.checkExtruderNr] < 60:
				self.startTemp = temp[self.checkExtruderNr]
				self.checkupState = 2
				wx.CallAfter(self.infoBox.SetInfo, _("Checking the heater and temperature sensor."))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S200 T%d' % (self.checkExtruderNr))
		elif self.checkupState == 2:
			#print "WARNING, TEMPERATURE TEST DISABLED FOR TESTING!"
			if temp[self.checkExtruderNr] > self.startTemp + 40:
				self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
				self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
				if self.checkExtruderNr < int(profile.getMachineSetting('extruder_amount')):
					self.checkExtruderNr = 0
					self.checkupState = 3
					wx.CallAfter(self.infoBox.SetAttention, _("Please make sure none of the endstops are pressed."))
					wx.CallAfter(self.endstopBitmap.Show, True)
					wx.CallAfter(self.Layout)
					self.comm.sendCommand('M119')
					wx.CallAfter(self.tempState.SetBitmap, self.checkBitmap)
				else:
					self.checkupState = 0
					self.checkExtruderNr += 1
			else:
				self.tempCheckTimeout -= 1
				if self.tempCheckTimeout < 1:
					self.checkupState = -1
					wx.CallAfter(self.tempState.SetBitmap, self.crossBitmap)
					wx.CallAfter(self.infoBox.SetError, _("Temperature measurement FAILED!"), 'http://wiki.ultimaker.com/Cura:_Temperature_measurement_problems')
					self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
					self.comm.sendCommand('M104 S0 T%d' % (self.checkExtruderNr))
		elif self.checkupState >= 3 and self.checkupState < 10:
			self.comm.sendCommand('M119')
		wx.CallAfter(self.temperatureLabel.SetLabel, _("Head temperature: %d") % (temp[self.checkExtruderNr]))

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			wx.CallAfter(self.commState.SetBitmap, self.checkBitmap)
			wx.CallAfter(self.machineState.SetLabel, _("Communication State: %s") % (self.comm.getStateString()))
		elif self.comm.isError():
			wx.CallAfter(self.commState.SetBitmap, self.crossBitmap)
			wx.CallAfter(self.infoBox.SetError, _("Failed to establish connection with the printer."), 'http://wiki.ultimaker.com/Cura:_Connection_problems')
			wx.CallAfter(self.endstopBitmap.Show, False)
			wx.CallAfter(self.machineState.SetLabel, '%s' % (self.comm.getErrorString()))
			wx.CallAfter(self.errorLogButton.Show, True)
			wx.CallAfter(self.Layout)
		else:
			wx.CallAfter(self.machineState.SetLabel, _("Communication State: %s") % (self.comm.getStateString()))

	def mcMessage(self, message):
		if self.checkupState >= 3 and self.checkupState < 10 and ('_min' in message or '_max' in message):
			for data in message.split(' '):
				if ':' in data:
					tag, value = data.split(':', 1)
					if tag == 'x_min':
						self.xMinStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'x_max':
						self.xMaxStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'y_min':
						self.yMinStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'y_max':
						self.yMaxStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'z_min':
						self.zMinStop = (value == 'H' or value == 'TRIGGERED')
					if tag == 'z_max':
						self.zMaxStop = (value == 'H' or value == 'TRIGGERED')
			if ':' in message:
				tag, value = map(str.strip, message.split(':', 1))
				if tag == 'x_min':
					self.xMinStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'x_max':
					self.xMaxStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'y_min':
					self.yMinStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'y_max':
					self.yMaxStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'z_min':
					self.zMinStop = (value == 'H' or value == 'TRIGGERED')
				if tag == 'z_max':
					self.zMaxStop = (value == 'H' or value == 'TRIGGERED')
			if 'z_max' in message:
				self.comm.sendCommand('M119')

			if self.checkupState == 3:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					if profile.getMachineSetting('machine_type') == 'ultimaker_plus':
						self.checkupState = 5
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the left X endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMinBitmap)
					else:
						self.checkupState = 4
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the right X endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMaxBitmap)
			elif self.checkupState == 4:
				if not self.xMinStop and self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 5
					wx.CallAfter(self.infoBox.SetAttention, _("Please press the left X endstop."))
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopXMinBitmap)
			elif self.checkupState == 5:
				if self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 6
					wx.CallAfter(self.infoBox.SetAttention, _("Please press the front Y endstop."))
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopYMinBitmap)
			elif self.checkupState == 6:
				if not self.xMinStop and not self.xMaxStop and self.yMinStop and not self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					if profile.getMachineSetting('machine_type') == 'ultimaker_plus':
						self.checkupState = 8
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the top Z endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMinBitmap)
					else:
						self.checkupState = 7
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the back Y endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopYMaxBitmap)
			elif self.checkupState == 7:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and self.yMaxStop and not self.zMinStop and not self.zMaxStop:
					self.checkupState = 8
					wx.CallAfter(self.infoBox.SetAttention, _("Please press the top Z endstop."))
					wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMinBitmap)
			elif self.checkupState == 8:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and self.zMinStop and not self.zMaxStop:
					if profile.getMachineSetting('machine_type') == 'ultimaker_plus':
						self.checkupState = 10
						self.comm.close()
						wx.CallAfter(self.infoBox.SetInfo, _("Checkup finished"))
						wx.CallAfter(self.infoBox.SetReadyIndicator)
						wx.CallAfter(self.endstopBitmap.Show, False)
						wx.CallAfter(self.stopState.SetBitmap, self.checkBitmap)
						wx.CallAfter(self.OnSkipClick, None)
					else:
						self.checkupState = 9
						wx.CallAfter(self.infoBox.SetAttention, _("Please press the bottom Z endstop."))
						wx.CallAfter(self.endstopBitmap.SetBitmap, self.endStopZMaxBitmap)
			elif self.checkupState == 9:
				if not self.xMinStop and not self.xMaxStop and not self.yMinStop and not self.yMaxStop and not self.zMinStop and self.zMaxStop:
					self.checkupState = 10
					self.comm.close()
					wx.CallAfter(self.infoBox.SetInfo, _("Checkup finished"))
					wx.CallAfter(self.infoBox.SetReadyIndicator)
					wx.CallAfter(self.endstopBitmap.Show, False)
					wx.CallAfter(self.stopState.SetBitmap, self.checkBitmap)
					wx.CallAfter(self.OnSkipClick, None)

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass


class UltimakerCalibrationPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCalibrationPage, self).__init__(parent, _("Ultimaker Calibration"))

		self.AddText("Your Ultimaker requires some calibration.")
		self.AddText("This calibration is needed for a proper extrusion amount.")
		self.AddSeperator()
		self.AddText("The following values are needed:")
		self.AddText("* Diameter of filament")
		self.AddText("* Number of steps per mm of filament extrusion")
		self.AddSeperator()
		self.AddText("The better you have calibrated these values, the better your prints\nwill become.")
		self.AddSeperator()
		self.AddText("First we need the diameter of your filament:")
		self.filamentDiameter = self.AddTextCtrl(profile.getProfileSetting('filament_diameter'))
		self.AddText(
			"If you do not own digital Calipers that can measure\nat least 2 digits then use 2.89mm.\nWhich is the average diameter of most filament.")
		self.AddText("Note: This value can be changed later at any time.")

	def StoreData(self):
		profile.putProfileSetting('filament_diameter', self.filamentDiameter.GetValue())


class UltimakerCalibrateStepsPerEPage(InfoPage):
	def __init__(self, parent):
		super(UltimakerCalibrateStepsPerEPage, self).__init__(parent, _("Ultimaker Calibration"))

		#if profile.getMachineSetting('steps_per_e') == '0':
		#	profile.putMachineSetting('steps_per_e', '865.888')

		self.AddText(_("Calibrating the Steps Per E requires some manual actions."))
		self.AddText(_("First remove any filament from your machine."))
		self.AddText(_("Next put in your filament so the tip is aligned with the\ntop of the extruder drive."))
		self.AddText(_("We'll push the filament 100mm"))
		self.extrudeButton = self.AddButton(_("Extrude 100mm filament"))
		self.AddText(_("Now measure the amount of extruded filament:\n(this can be more or less then 100mm)"))
		self.lengthInput, self.saveLengthButton = self.AddTextCtrlButton("100", _("Save"))
		self.AddText(_("This results in the following steps per E:"))
		self.stepsPerEInput = self.AddTextCtrl(profile.getMachineSetting('steps_per_e'))
		self.AddText(_("You can repeat these steps to get better calibration."))
		self.AddSeperator()
		self.AddText(
			_("If you still have filament in your printer which needs\nheat to remove, press the heat up button below:"))
		self.heatButton = self.AddButton(_("Heatup for filament removal"))

		self.saveLengthButton.Bind(wx.EVT_BUTTON, self.OnSaveLengthClick)
		self.extrudeButton.Bind(wx.EVT_BUTTON, self.OnExtrudeClick)
		self.heatButton.Bind(wx.EVT_BUTTON, self.OnHeatClick)

	def OnSaveLengthClick(self, e):
		currentEValue = float(self.stepsPerEInput.GetValue())
		realExtrudeLength = float(self.lengthInput.GetValue())
		newEValue = currentEValue * 100 / realExtrudeLength
		self.stepsPerEInput.SetValue(str(newEValue))
		self.lengthInput.SetValue("100")

	def OnExtrudeClick(self, e):
		t = threading.Thread(target=self.OnExtrudeRun)
		t.daemon = True
		t.start()

	def OnExtrudeRun(self):
		self.heatButton.Enable(False)
		self.extrudeButton.Enable(False)
		currentEValue = float(self.stepsPerEInput.GetValue())
		self.comm = machineCom.MachineCom()
		if not self.comm.isOpen():
			wx.MessageBox(
				_("Error: Failed to open serial port to machine\nIf this keeps happening, try disconnecting and reconnecting the USB cable"),
				'Printer error', wx.OK | wx.ICON_INFORMATION)
			self.heatButton.Enable(True)
			self.extrudeButton.Enable(True)
			return
		while True:
			line = self.comm.readline()
			if line == '':
				return
			if 'start' in line:
				break
			#Wait 3 seconds for the SD card init to timeout if we have SD in our firmware but there is no SD card found.
		time.sleep(3)

		self.sendGCommand('M302') #Disable cold extrusion protection
		self.sendGCommand("M92 E%f" % (currentEValue))
		self.sendGCommand("G92 E0")
		self.sendGCommand("G1 E100 F600")
		time.sleep(15)
		self.comm.close()
		self.extrudeButton.Enable()
		self.heatButton.Enable()

	def OnHeatClick(self, e):
		t = threading.Thread(target=self.OnHeatRun)
		t.daemon = True
		t.start()

	def OnHeatRun(self):
		self.heatButton.Enable(False)
		self.extrudeButton.Enable(False)
		self.comm = machineCom.MachineCom()
		if not self.comm.isOpen():
			wx.MessageBox(
				_("Error: Failed to open serial port to machine\nIf this keeps happening, try disconnecting and reconnecting the USB cable"),
				'Printer error', wx.OK | wx.ICON_INFORMATION)
			self.heatButton.Enable(True)
			self.extrudeButton.Enable(True)
			return
		while True:
			line = self.comm.readline()
			if line == '':
				self.heatButton.Enable(True)
				self.extrudeButton.Enable(True)
				return
			if 'start' in line:
				break
			#Wait 3 seconds for the SD card init to timeout if we have SD in our firmware but there is no SD card found.
		time.sleep(3)

		self.sendGCommand('M104 S200') #Set the temperature to 200C, should be enough to get PLA and ABS out.
		wx.MessageBox(
			'Wait till you can remove the filament from the machine, and press OK.\n(Temperature is set to 200C)',
			'Machine heatup', wx.OK | wx.ICON_INFORMATION)
		self.sendGCommand('M104 S0')
		time.sleep(1)
		self.comm.close()
		self.heatButton.Enable(True)
		self.extrudeButton.Enable(True)

	def sendGCommand(self, cmd):
		self.comm.sendCommand(cmd) #Disable cold extrusion protection
		while True:
			line = self.comm.readline()
			if line == '':
				return
			if line.startswith('ok'):
				break

	def StoreData(self):
		profile.putPreference('steps_per_e', self.stepsPerEInput.GetValue())

class Ultimaker2ReadyPage(InfoPage):
	def __init__(self, parent):
		super(Ultimaker2ReadyPage, self).__init__(parent, _("Ultimaker2"))
		self.AddText(_('Congratulations on your the purchase of your brand new Ultimaker2.'))
		self.AddText(_('Cura is now ready to be used with your Ultimaker2.'))
		self.AddSeperator()

class LulzbotMachineSelectPage(InfoPage):
	IMAGE_WIDTH=300
	IMAGE_HEIGHT=200

	def __init__(self, parent):
		super(LulzbotMachineSelectPage, self).__init__(parent, _("Select your machine"))

		self.panel = self.AddPanel()

		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.LulzbotMini = self.AddImageButton(self.panel, 0, 0, _("LulzBot Mini"),
											   'Lulzbot_mini.jpg', image_size, style=ImageButton.IB_GROUP)
		self.LulzbotMini.OnSelected(self.OnLulzbotMiniSelected)

		self.LulzbotTaz6 = self.AddImageButton(self.panel, 0, 1, _("LulzBot TAZ 6"),
											   'Lulzbot_TAZ6.jpg', image_size)
		self.LulzbotTaz6.OnSelected(self.OnLulzbotTaz6Selected)

		self.LulzbotTaz = self.AddImageButton(self.panel, 1, 0, _("LulzBot TAZ 4 or 5"),
											   'Lulzbot_TAZ5.jpg', image_size)
		self.LulzbotTaz.OnSelected(self.OnLulzbotTazSelected)

		self.OtherPrinters = self.AddImageButton(self.panel, 1, 1, _("Other Printers"),
												 'Generic-3D-Printer.png', image_size)
		self.OtherPrinters.OnSelected(self.OnOthersSelected)
		self.LulzbotMini.SetValue(True)

	def OnPageShown(self):
		self.LulzbotMini.TriggerGroupCallbacks()

	def OnOthersSelected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().machineSelectPage)

	def OnLulzbotMiniSelected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotMiniToolheadPage)

	def OnLulzbotTaz6Selected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTaz6ToolheadTypePage)

	def OnLulzbotTazSelected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTazSelectPage)

	def AllowNext(self):
		return True

	def AllowBack(self):
		return False

	def StoreData(self):
		if self.LulzbotTaz.GetValue() or self.LulzbotMini.GetValue() or self.LulzbotTaz6.GetValue():
			if self.LulzbotTaz.GetValue():
				profile.putMachineSetting('machine_width', '290')
				profile.putMachineSetting('machine_depth', '275')
				profile.putMachineSetting('machine_height', '250')
				profile.putMachineSetting('serial_baud', '115200')
				profile.putMachineSetting('extruder_head_size_min_x', '0.0')
				profile.putMachineSetting('extruder_head_size_max_x', '0.0')
				profile.putMachineSetting('extruder_head_size_min_y', '0.0')
				profile.putMachineSetting('extruder_head_size_max_y', '0.0')
				profile.putMachineSetting('extruder_head_size_height', '0.0')
			elif self.LulzbotTaz6.GetValue():
				profile.putMachineSetting('machine_width', '280')
				profile.putMachineSetting('machine_depth', '280')
				profile.putMachineSetting('machine_height', '250')
				profile.putMachineSetting('serial_baud', '250000')
				profile.putMachineSetting('extruder_head_size_min_x', '0.0')
				profile.putMachineSetting('extruder_head_size_max_x', '0.0')
				profile.putMachineSetting('extruder_head_size_min_y', '0.0')
				profile.putMachineSetting('extruder_head_size_max_y', '0.0')
				profile.putMachineSetting('extruder_head_size_height', '0.0')
			else:
				# Nozzle diameter and machine type will be set in the toolhead selection page
				profile.putMachineSetting('machine_name', 'LulzBot Mini')
				profile.putMachineSetting('machine_width', '155')
				profile.putMachineSetting('machine_depth', '155')
				profile.putMachineSetting('machine_height', '158')
				profile.putMachineSetting('serial_baud', '115200')
				profile.putMachineSetting('extruder_head_size_min_x', '40')
				profile.putMachineSetting('extruder_head_size_max_x', '75')
				profile.putMachineSetting('extruder_head_size_min_y', '25')
				profile.putMachineSetting('extruder_head_size_max_y', '55')
				profile.putMachineSetting('extruder_head_size_height', '17')

			profile.putMachineSetting('machine_center_is_zero', 'False')
			profile.putMachineSetting('gcode_flavor', 'RepRap (Marlin/Sprinter)')
			profile.putMachineSetting('has_heated_bed', 'True')
			profile.putProfileSetting('retraction_enable', 'True')
			profile.putPreference('startMode', 'Simple')
			profile.putProfileSetting('wall_thickness', float(profile.getProfileSetting('nozzle_size')) * 2)
			profile.checkAndUpdateMachineName()

class LulzbotReadyPage(InfoPage):
	def __init__(self, parent):
		super(LulzbotReadyPage, self).__init__(parent, _("LulzBot TAZ/Mini"))
		self.AddText(_('Cura is now ready to be used with your LulzBot 3D printer.'))
		self.AddSeperator()
		self.AddText(_('Complete tool head installation and calibration by following'))
		self.AddTextUrl(_('instructions available here '), 'ohai.LulzBot.com/group/accessories', 'http://ohai.lulzbot.com/group/accessories')
		self.AddText('')
		self.AddText(_('Please contact support if you have problems operating'))
		self.AddTextUrl(_('your LulzBot 3D Printer :'), 'www.LulzBot.com/support', 'http://www.lulzbot.com/support')
		self.AddSeperator()

class LulzbotMiniToolheadSelectPage(InfoPage):
	def __init__(self, parent, allowBack = True):
		super(LulzbotMiniToolheadSelectPage, self).__init__(parent, _("LulzBot Mini Tool Head Selection"))

		self.allowBack = allowBack
		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.standard = self.AddImageButton(self.panel, 0, 0, _('Standard LulzBot Mini'),
											'Lulzbot_mini.jpg', image_size,
											style=ImageButton.IB_GROUP)
		self.flexy = self.AddImageButton(self.panel, 0, 1, _('LulzBot Mini with Flexystruder'),
											'Lulzbot_Toolhead_Mini_Flexystruder.jpg', image_size)
		self.standard.SetValue(True)

	def AllowBack(self):
		return self.allowBack

	def StoreData(self):
		if self.standard.GetValue():
			profile.putProfileSetting('nozzle_size', '0.5')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Single Extruder v2')
			profile.putMachineSetting('toolhead_shortname', '')
			profile.putMachineSetting('machine_type', 'lulzbot_mini')
		else:
			profile.putProfileSetting('nozzle_size', '0.6')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Flexystruder v2')
			profile.putMachineSetting('toolhead_shortname', 'Flexystruder')
			profile.putMachineSetting('machine_type', 'lulzbot_mini_flexystruder')

class LulzbotTaz6ToolheadTypeSelectPage(InfoPage):
	def __init__(self, parent, allowBack = True):
		super(LulzbotTaz6ToolheadTypeSelectPage, self).__init__(parent, _("LulzBot TAZ 6 Tool Head Selection"))
		self.allowBack = allowBack

		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.single = self.AddImageButton(self.panel, 0, 0, _('Single Extruder'),
										'LulzBot_SingleExtruder_icon.jpg', image_size,
										style=ImageButton.IB_GROUP)
		self.single.OnSelected(self.OnSingleSelected)
		self.dual = self.AddImageButton(self.panel, 0, 1, _('Dual Extruder'),
										'LulzBot_DualExtruder_icon.jpg', image_size)
		self.dual.OnSelected(self.OnDualSelected)
		self.single.SetValue(True) #Set the default selection

	def OnSingleSelected(self):
		self.GetParent().lulzbotTaz6ToolheadPage.SetSingleType()

	def OnDualSelected(self):
		self.GetParent().lulzbotTaz6ToolheadPage.SetDualType()

	def AllowBack(self):
		return self.allowBack

	def StoreData(self):
		pass

class LulzbotTaz6ToolheadSelectPage(InfoPage):
	def __init__(self, parent, allowNext = False):
		super(LulzbotTaz6ToolheadSelectPage, self).__init__(parent, _("LulzBot TAZ 6 Tool Head Selection"))
		self.allowNext = allowNext

		self.panel = None
		self.SetSingleType()

	def _deletePanel(self):
		if self.panel:
			self.panel.GetSizer().Clear(True)
			self.GetSizer().Detach(self.panel)
			self.panel.Destroy()
			self.rowNr -= 1
		self.panel = None
		self.standard = None
		self.flexy = None
		self.moar = None
		self.dual = None
		self.flexydual = None

	def SetSingleType(self):
		self._deletePanel()
		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.standard = self.AddImageButton(self.panel, 0, 0, _('Single Extruder v2.1'),
										'Lulzbot_Toolhead_TAZ6_Single-v2.1.jpg', image_size,
										style=ImageButton.IB_GROUP)
		self.standard.OnSelected(self.OnStandardSelected)
		self.flexy = self.AddImageButton(self.panel, 0, 1, _('Flexystruder v2'),
										'Lulzbot_Toolhead_TAZ_Flexystruder_v2.jpg', image_size)
		self.moar = self.AddImageButton(self.panel, 1, 0, _('MOARstruder'),
										'Lulzbot_Toolhead_TAZ_MOARstruder.jpg', image_size)
		self.flexy.OnSelected(self.OnNonStandardSelected)
		self.moar.OnSelected(self.OnNonStandardSelected)
		if self.standard.GetValue() == False and \
		   self.flexy.GetValue() == False and \
		   self.moar.GetValue() == False:
			self.standard.SetValue(True) #Set the default selection
		self.Layout()

	def SetDualType(self):
		self._deletePanel()
		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.dual = self.AddImageButton(self.panel, 0, 0, _('Dual Extruder v2'),
										'Lulzbot_Toolhead_TAZ_Dual_Extruder_v2.jpg', image_size,
										style=ImageButton.IB_GROUP)
		self.flexydual = self.AddImageButton(self.panel, 0, 1, _('FlexyDually v2'),
										'Lulzbot_Toolhead_TAZ_FlexyDually_v2.jpg', image_size)
		self.dual.OnSelected(self.OnNonStandardSelected)
		self.flexydual.OnSelected(self.OnNonStandardSelected)
		if self.dual.GetValue() == False and \
		   self.flexydual.GetValue() == False:
			self.dual.SetValue(True) #Set the default selection
		self.Layout()

	def ReloadCurrentPage(self):
		if self == self.GetParent().GetCurrentPage():
			self.GetParent().ShowPage(self)

	def OnStandardSelected(self):
		if self.allowNext:
			wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotFirmwarePage)
		else:
			self.SetNext(None)
		# This is needed so the wizard will change its Next button into Finished if needed
		self.ReloadCurrentPage()

	def OnNonStandardSelected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotFirmwarePage)
		# This is needed so the wizard will change its Finished button into Next if needed
		self.ReloadCurrentPage()

	def StoreData(self):
		profile.putMachineSetting('machine_name', 'LulzBot TAZ 6')
		machine_type = 'lulzbot_TAZ_6'
		if self.standard and self.standard.GetValue():
			profile.putProfileSetting('nozzle_size',  '0.5')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Single Extruder V2.1')
			profile.putMachineSetting('toolhead_shortname', 'Single v2.1')
			profile.putMachineSetting('machine_type', machine_type + '_Single_v2.1')
		elif self.flexy and self.flexy.GetValue():
			profile.putProfileSetting('nozzle_size', '0.6')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Flexystruder V2')
			profile.putMachineSetting('toolhead_shortname', 'Flexystruder v2')
			profile.putMachineSetting('machine_type', machine_type + '_Flexystruder_v2')
		elif self.moar and self.moar.GetValue():
			profile.putProfileSetting('nozzle_size', '1.2')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'MOARstruder')
			profile.putMachineSetting('toolhead_shortname', 'MOARstruder')
			profile.putMachineSetting('machine_type', machine_type + '_Moarstruder')
		elif self.dual and self.dual.GetValue():
			profile.putProfileSetting('nozzle_size', '0.5')
			profile.putMachineSetting('extruder_amount', '2')
			profile.putMachineSetting('extruder_offset_x1', '0.0')
			profile.putMachineSetting('extruder_offset_y1', '-50.00')
			profile.putMachineSetting('toolhead', 'Dual Extruder V2')
			profile.putMachineSetting('toolhead_shortname', 'Dual v2')
			profile.putMachineSetting('machine_type', machine_type + '_Dual_v2')
		else: #self.flexydual.GetValue():
			profile.putProfileSetting('nozzle_size', '0.6')
			profile.putMachineSetting('extruder_amount', '2')
			profile.putMachineSetting('extruder_offset_x1', '0.0')
			profile.putMachineSetting('extruder_offset_y1', '-50.00')
			profile.putMachineSetting('toolhead', 'FlexyDually V2')
			profile.putMachineSetting('toolhead_shortname', 'FlexyDually v2')
			profile.putMachineSetting('machine_type', machine_type + '_FlexyDually_v2')

class LulzbotTazSelectPage(InfoPage):
	def __init__(self, parent):
		super(LulzbotTazSelectPage, self).__init__(parent, _("LulzBot TAZ 4-5 Selection"))

		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.taz5 = self.AddImageButton(self.panel, 0, 0, _('Stock TAZ 5 (PEI && v2)'),
										'Lulzbot_TAZ_5_Hex_and_PEI.jpg', image_size,
										style=ImageButton.IB_GROUP)
		self.taz5.OnSelected(self.OnTaz5Selected)
		self.taz4 = self.AddImageButton(self.panel, 0, 1, _('Stock TAZ 4 (PET && v1)'),
										'Lulzbot_TAZ_4_Buda_and_PET.jpg', image_size)
		self.taz4.OnSelected(self.OnTaz4Selected)
		self.modified = self.AddImageButton(self.panel, 1, 0, _('Modified LulzBot TAZ 4 or 5'),
											'Lulzbot_TAZ5.jpg', image_size)
		self.modified.OnSelected(self.OnModifiedSelected)
		self.taz5.SetValue(True)
		self.showing_page = False

	def OnPageShown(self):
		# We'll end up with an infinite recursion if we do this while calling ShowPage locally
		if not self.showing_page:
			self.taz5.TriggerGroupCallbacks()

	def ReloadCurrentPage(self):
		# Don't show the page if it's not the current one, otherwise we might
		# show the page during __init__ which will cause a StoreData to be called
		# when we run the wizard (possibly for a different machine type)
		if self == self.GetParent().GetCurrentPage():
			self.showing_page = True
			self.GetParent().ShowPage(self)
			self.showing_page = False

	def OnTaz5Selected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTaz5NozzleSelectPage)
		# This is needed so the wizard will change its Finished button into Next if needed
		self.ReloadCurrentPage()

	def OnTaz4Selected(self):
		self.SetNext(None)
		# This is needed so the wizard will change its Next button into Finished if needed
		self.ReloadCurrentPage()

	def OnModifiedSelected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTazBedSelectPage)
		wx.wizard.WizardPageSimple.Chain(self.GetParent().lulzbotTazBedSelectPage,
										 self.GetParent().lulzbotTazHotendPage)
		# This is needed so the wizard will change its Finished button into Next if needed
		self.ReloadCurrentPage()

	def StoreData(self):
		if self.taz5.GetValue():
			profile.putProfileSetting('nozzle_size',  '0.5')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Single Extruder V2')
			profile.putMachineSetting('toolhead_shortname', '')
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_5_SingleV2')
			profile.putMachineSetting('machine_name', 'LulzBot TAZ 5')
		elif self.taz4.GetValue():
			profile.putProfileSetting('nozzle_size', '0.35')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Single Extruder V1')
			profile.putMachineSetting('toolhead_shortname', '')
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_4_SingleV1')
			profile.putMachineSetting('machine_name', 'LulzBot TAZ 4')

class LulzbotTazBedSelectPage(InfoPage):
	def __init__(self, parent):
		super(LulzbotTazBedSelectPage, self).__init__(parent, _("Bed Surface"))

		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.pei = self.AddImageButton(self.panel, 0, 0, _('PEI'),
									   'Lulzbot_TAZ_PEI_Bed.jpg', image_size,
									   style=ImageButton.IB_GROUP)
		self.pet = self.AddImageButton(self.panel, 0, 1, _('PET'),
									   'Lulzbot_TAZ_PET_Bed.jpg', image_size)
		self.pei.SetValue(True)

	def StoreData(self):
		if self.pei.GetValue():
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_5')
			profile.putMachineSetting('machine_name', 'LulzBot TAZ 5')
		else:
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_4')
			profile.putMachineSetting('machine_name', 'LulzBot TAZ 4')

class LulzbotTazToolheadTypeSelectPage(InfoPage):
	def __init__(self, parent):
		super(LulzbotTazToolheadTypeSelectPage, self).__init__(parent, _("LulzBot TAZ Tool Head Selection"))
		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.single = self.AddImageButton(self.panel, 0, 0, _('Single Extruder'),
										'LulzBot_SingleExtruder_icon.jpg', image_size,
										style=ImageButton.IB_GROUP)
		self.dual = self.AddImageButton(self.panel, 0, 1, _('Dual Extruder'),
										'LulzBot_DualExtruder_icon.jpg', image_size)
		self.single.SetValue(True) #Set the default selection

	def StoreData(self):
		if self.single.GetValue():
			self.GetParent().lulzbotTazToolheadPage.SetSingleType()
		else:
			self.GetParent().lulzbotTazToolheadPage.SetDualType()

class LulzbotTazToolheadSelectPage(InfoPage):
	def __init__(self, parent):
		super(LulzbotTazToolheadSelectPage, self).__init__(parent, _("LulzBot TAZ Tool Head Selection"))

		self.panel = None
		self.version = 1
		self.type = ["single", "dual"]
		self.SetVersion(1)
		self.single.SetValue(True)

	def _deletePanel(self):
		if self.panel:
			self.panel.GetSizer().Clear(True)
			self.GetSizer().Detach(self.panel)
			self.panel.Destroy()
			self.rowNr -= 1
		self.panel = None
		self.single = None
		self.flexy = None
		self.moar = None
		self.dually = None
		self.flexydually = None

	def _buildPanel(self):
		self._deletePanel()
		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		shift = 0
		if "single" in self.type or self.version == 1:
			self.single = self.AddImageButton(self.panel, 0, 0, _('Single Extruder v%d'% self.version),
											  'Lulzbot_Toolhead_TAZ_Single_v%d.jpg' % self.version, image_size,
											  style=ImageButton.IB_GROUP)
			self.flexy = self.AddImageButton(self.panel, 0, 1, _('Flexystruder v%d'% self.version),
											 'Lulzbot_Toolhead_TAZ_Flexystruder_v%d.jpg'% self.version, image_size)
			if self.version == 2 and "dual" not in self.type and \
			   profile.getMachineSetting('machine_type').startswith('lulzbot_TAZ_5'):
				self.moar = self.AddImageButton(self.panel, 1, 0, _('MOARstruder'),
												'Lulzbot_Toolhead_TAZ_MOARstruder.jpg', image_size)
			shift = 1
		if "dual" in self.type or self.version == 1:
			self.dually = self.AddImageButton(self.panel, shift, 0, _('Dual Extruder v%d' % self.version),
											  'Lulzbot_Toolhead_TAZ_Dual_Extruder_v%d.jpg' % self.version, image_size,
											  style=ImageButton.IB_GROUP if shift == 0 else None)
			self.flexydually = self.AddImageButton(self.panel, shift, 1, _('FlexyDually v%d' % self.version),
												   'Lulzbot_Toolhead_TAZ_FlexyDually_v%d.jpg' % self.version, image_size)
		if (self.single is None or self.single.GetValue() == False) and \
		   (self.flexy is None or self.flexy.GetValue() == False) and \
		   (self.moar is None or self.moar.GetValue() == False) and \
		   (self.dually is None or self.dually.GetValue() == False) and \
		   (self.flexydually is None or self.flexydually.GetValue() == False):
			if self.single:
				self.single.SetValue(True) #Set the default selection
			else:
				self.dually.SetValue(True) #Set the default selection
		self.Layout()
		if self.version == 1:
			self.single.OnSelected(None)
			self.flexy.OnSelected(None)
			self.dually.OnSelected(None)
			self.flexydually.OnSelected(None)
			wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotFirmwarePage)
		elif self.version == 2:
			if "single" in self.type:
				self.single.OnSelected(self.OnSingleV2)
				self.flexy.OnSelected(self.OnNonSingle)
				if self.moar:
					self.moar.OnSelected(self.OnNonSingle)
				if self.single.GetValue():
					wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTaz5NozzleSelectPage)
					wx.wizard.WizardPageSimple.Chain(self.GetParent().lulzbotTaz5NozzleSelectPage, self.GetParent().lulzbotFirmwarePage)
				else:
					wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotFirmwarePage)
			else:
				self.dually.OnSelected(self.OnNonSingle)
				self.flexydually.OnSelected(self.OnNonSingle)
				wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotFirmwarePage)
		wx.wizard.WizardPageSimple.Chain(self.GetParent().lulzbotFirmwarePage, self.GetParent().lulzbotReadyPage)

	def SetSingleType(self):
		self.type = ["single"]
		self._buildPanel()

	def SetDualType(self):
		self.type = ["dual"]
		self._buildPanel()

	def SetBothType(self):
		self.type = ["dual", "single"]
		self._buildPanel()

	def SetVersion(self, version):
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.version = version
		self._buildPanel()

	def OnSingleV2(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTaz5NozzleSelectPage)
		wx.wizard.WizardPageSimple.Chain(self.GetParent().lulzbotTaz5NozzleSelectPage, self.GetParent().lulzbotFirmwarePage)

	def OnNonSingle(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotFirmwarePage)

	def StoreData(self):
		if profile.getMachineSetting('machine_type').startswith('lulzbot_TAZ_4'):
			taz_version = 4
		else:
			taz_version = 5
		version = (taz_version, self.version)
		if self.single and self.single.GetValue():
			profile.putProfileSetting('nozzle_size', '0.5' if self.version == 2 else '0.35')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Single Extruder V%d' % self.version)
			profile.putMachineSetting('toolhead_shortname', '')
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_%d_SingleV%d' % version)
			# on TAZ5, MOARstruder reduces the build volume, so we need to restore it
			profile.putMachineSetting('machine_width', '290')
			profile.putMachineSetting('machine_height', '250')
		elif self.flexy and self.flexy.GetValue():
			profile.putProfileSetting('nozzle_size', '0.6')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'Flexystruder V%d' % self.version)
			profile.putMachineSetting('toolhead_shortname', 'Flexystruder v%d' % self.version)
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_%d_FlexystruderV%d' % version)
			# on TAZ5, MOARstruder reduces the build volume, so we need to restore it
			profile.putMachineSetting('machine_width', '290')
			profile.putMachineSetting('machine_height', '250')
		elif self.moar and self.moar.GetValue():
			profile.putProfileSetting('nozzle_size', '1.2')
			profile.putMachineSetting('extruder_amount', '1')
			profile.putMachineSetting('toolhead', 'MOARstruder')
			profile.putMachineSetting('toolhead_shortname', 'MOARstruder')
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_5_Moarstruder')
			# on TAZ5, MOARstruder reduces the build volume
			profile.putMachineSetting('machine_width', '280')
			profile.putMachineSetting('machine_height', '242')
		elif self.dually and self.dually.GetValue():
			profile.putProfileSetting('nozzle_size', '0.5')
			profile.putMachineSetting('extruder_amount', '2')
			profile.putMachineSetting('extruder_offset_x1', '0.0')
			profile.putMachineSetting('extruder_offset_y1', '-50.0' if self.version == 2 else '-52.00')
			profile.putMachineSetting('toolhead', 'Dual Extruder V%d' % self.version)
			profile.putMachineSetting('toolhead_shortname', 'Dual v%d' % self.version)
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_%d_DualV%d' % version)
			# on TAZ5, MOARstruder reduces the build volume, so we need to restore it
			profile.putMachineSetting('machine_width', '290')
			profile.putMachineSetting('machine_height', '250')
		elif self.flexydually and self.flexydually.GetValue():
			profile.putProfileSetting('nozzle_size', '0.6')
			profile.putMachineSetting('extruder_amount', '2')
			profile.putMachineSetting('extruder_offset_x1', '0.0')
			profile.putMachineSetting('extruder_offset_y1', '-50.0' if self.version == 2 else '-52.00')
			profile.putMachineSetting('toolhead', 'FlexyDually V%d' % self.version)
			profile.putMachineSetting('toolhead_shortname', 'FlexyDually v%d' % self.version)
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_%d_FlexyDuallyV%d' % version)
			# on TAZ5, MOARstruder reduces the build volume, so we need to restore it
			profile.putMachineSetting('machine_width', '290')
			profile.putMachineSetting('machine_height', '250')

class LulzbotHotendSelectPage(InfoPage):
	def __init__(self, parent, allowBack = True):
		super(LulzbotHotendSelectPage, self).__init__(parent, _("LulzBot Tool Head Hot end Selection"))

		self.allowBack = allowBack
		self.panel = self.AddPanel()
		image_size=(LulzbotMachineSelectPage.IMAGE_WIDTH, LulzbotMachineSelectPage.IMAGE_HEIGHT)
		self.v1 = self.AddImageButton(self.panel, 0, 0, _('v1 (Budaschnozzle)'),
											'Lulzbot_Toolhead_v1.jpg', image_size,
											style=ImageButton.IB_GROUP)
		self.v2 = self.AddImageButton(self.panel, 0, 1, _('v2 (LulzBot Hexagon)'),
											'Lulzbot_Toolhead_v2.jpg', image_size)
		self.v1.OnSelected(self.OnV1Selected)
		self.v2.OnSelected(self.OnV2Selected)
		self.v1.SetValue(True)

	def OnV1Selected(self):
		wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTazToolheadPage)

	def OnV2Selected(self):
		if profile.getMachineSetting('machine_type').startswith('lulzbot_TAZ_4'):
			wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTazToolheadPage)
			self.GetParent().lulzbotTazToolheadPage.SetBothType()
		else:
			wx.wizard.WizardPageSimple.Chain(self, self.GetParent().lulzbotTazToolheadTypePage)
			wx.wizard.WizardPageSimple.Chain(self.GetParent().lulzbotTazToolheadTypePage, self.GetParent().lulzbotTazToolheadPage)

	def OnPageShown(self):
		if self.v1.GetValue():
			self.OnV1Selected()
		else:
			self.OnV2Selected()

	def AllowBack(self):
		return self.allowBack

	def StoreData(self):
		self.GetParent().lulzbotTazToolheadPage.SetVersion(1 if self.v1.GetValue() else 2)

class LulzbotTaz5NozzleSelectPage(InfoPage):

	def __init__(self, parent):
		super(LulzbotTaz5NozzleSelectPage, self).__init__(parent, _("LulzBot TAZ Single v2 Nozzle Selection"))

		self.AddText(_('Please select your LulzBot Hexagon Hot End\'s nozzle diameter:'))
		self.Nozzle35Radio = self.AddRadioButton("0.35 mm", style=wx.RB_GROUP)
		self.Nozzle35Radio.SetValue(True)
		self.Nozzle50Radio = self.AddRadioButton("0.5 mm")
		self.AddText(_(' '))
		self.AddSeperator()

		self.AddText(_('If you are not sure which nozzle diameter you have,'))
		self.AddTextUrl(_('please check this webpage: '), 'LulzBot.com/printer-identification', 'http://lulzbot.com/printer-identification')

	def StoreData(self):
		if profile.getMachineSetting('machine_type').startswith('lulzbot_TAZ_4'):
			taz_version = 4
		else:
			taz_version = 5
		if self.Nozzle35Radio.GetValue():
			profile.putProfileSetting('nozzle_size', '0.35')
			profile.putMachineSetting('toolhead', 'Single Extruder v2 (0.35mm nozzle)')
			profile.putMachineSetting('toolhead_shortname', '0.35 nozzle')
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_%d_035nozzle' % taz_version)

		else:
			profile.putProfileSetting('nozzle_size', '0.5')
			profile.putMachineSetting('toolhead', 'Single Extruder v2 (0.5mm nozzle)')
			profile.putMachineSetting('toolhead_shortname', '0.5 nozzle')
			profile.putMachineSetting('machine_type', 'lulzbot_TAZ_%d_05nozzle' % taz_version)

class LulzbotFirmwareUpdatePage(InfoPage):
	def __init__(self, parent):
		super(LulzbotFirmwareUpdatePage, self).__init__(parent, _("LulzBot Firmware Update"))

		self.AddText(_("Your LulzBot printer\'s firmware will now be updated.\n" +
		"Note: this will overwrite your existing firmware."))
		self.AddSeperator()
		self.AddText(_("Follow these steps to prevent writing firmware to the wrong device:\n" +
					   "    1) Unplug all USB devices from your computer\n" +
					   "    2) Plug your 3D Printer into the computer with a USB cable\n" +
					   "    3) Turn on your 3D Printer\n" +
					   "    4) Click \"Flash the firmware\""))
		self.AddHiddenSeperator()
		upgradeButton, skipUpgradeButton = self.AddDualButton(_('Flash the firmware'), _('Skip upgrade'))
		upgradeButton.Bind(wx.EVT_BUTTON, self.OnUpgradeClick)
		skipUpgradeButton.Bind(wx.EVT_BUTTON, self.OnSkipClick)

	def AllowNext(self):
		return version.isDevVersion()

	def OnUpgradeClick(self, e):
		if firmwareInstall.InstallFirmware():
			self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()
			self.GetParent().ShowPage(self.GetNext())

	def OnSkipClick(self, e):
		dlg = wx.MessageDialog(self,
			_("CAUTION: Updating firmware is necessary when changing the\n" \
			  "tool head on your LulzBot desktop 3D Printer." \
			  "\n\n" +
			  "Are you sure you want to skip the firmware update?"),
			_('Skip firmware update?'),
			wx.YES_NO | wx.ICON_EXCLAMATION)
		skip = dlg.ShowModal() == wx.ID_YES
		dlg.Destroy()
		if skip:
			self.GetParent().FindWindowById(wx.ID_FORWARD).Enable()
			self.GetParent().ShowPage(self.GetNext())

class LulzbotChangeToolheadWizard(wx.wizard.Wizard):
	def __init__(self):
		super(LulzbotChangeToolheadWizard, self).__init__(None, -1, _("Change LulzBot Tool Head Wizard"))

		self._nozzle_size = profile.getProfileSettingFloat('nozzle_size')
		self._machine_name = profile.getMachineSetting('machine_name')
		self._machine_type = profile.getMachineSetting('machine_type')
		self._toolhead = profile.getMachineSetting('toolhead')
		self._toolhead_shortname = profile.getMachineSetting('toolhead_shortname')
		self._extruder_amount = int(profile.getMachineSettingFloat('extruder_amount'))
		self._extruder_offset_x1 = float(profile.getMachineSettingFloat('extruder_offset_x1'))
		self._extruder_offset_y1 = float(profile.getMachineSettingFloat('extruder_offset_y1'))
		self._machine_width = float(profile.getMachineSettingFloat('machine_width'))
		self._machine_height = float(profile.getMachineSettingFloat('machine_height'))

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
		self.Bind(wx.wizard.EVT_WIZARD_CANCEL, self.OnCancel)

		self.lulzbotReadyPage = LulzbotReadyPage(self)
		self.lulzbotFirmwarePage = LulzbotFirmwareUpdatePage(self)
		self.lulzbotMiniToolheadPage = LulzbotMiniToolheadSelectPage(self, False)
		self.lulzbotTazToolheadPage = LulzbotTazToolheadSelectPage(self)
		self.lulzbotTaz6ToolheadPage = LulzbotTaz6ToolheadSelectPage(self, True)
		self.lulzbotTazToolheadTypePage = LulzbotTazToolheadTypeSelectPage(self)
		self.lulzbotTaz6ToolheadTypePage = LulzbotTaz6ToolheadTypeSelectPage(self, False)
		self.lulzbotTazHotendPage = LulzbotHotendSelectPage(self, False)
		self.lulzbotTaz5NozzleSelectPage = LulzbotTaz5NozzleSelectPage(self)
		self.lulzbotTazBedSelectPage = LulzbotTazBedSelectPage(self)
		self.lulzbotTazSelectPage = LulzbotTazSelectPage(self)

		wx.wizard.WizardPageSimple.Chain(self.lulzbotTazHotendPage, self.lulzbotTazToolheadTypePage)
		wx.wizard.WizardPageSimple.Chain(self.lulzbotTazToolheadTypePage, self.lulzbotTazToolheadPage)
		wx.wizard.WizardPageSimple.Chain(self.lulzbotTaz6ToolheadTypePage, self.lulzbotTaz6ToolheadPage)
		wx.wizard.WizardPageSimple.Chain(self.lulzbotTazToolheadTypePage, self.lulzbotTazToolheadPage)
		wx.wizard.WizardPageSimple.Chain(self.lulzbotTaz6ToolheadPage, self.lulzbotFirmwarePage)
		wx.wizard.WizardPageSimple.Chain(self.lulzbotFirmwarePage, self.lulzbotReadyPage)


		if profile.getMachineSetting('machine_type').startswith('lulzbot_mini'):
			wx.wizard.WizardPageSimple.Chain(self.lulzbotMiniToolheadPage, self.lulzbotReadyPage)
			self.RunWizard(self.lulzbotMiniToolheadPage)
		elif profile.getMachineSetting('machine_type').startswith('lulzbot_TAZ_5') or \
                     profile.getMachineSetting('machine_type').startswith('lulzbot_TAZ_4'):
			self.RunWizard(self.lulzbotTazHotendPage)
		elif profile.getMachineSetting('machine_type').startswith('lulzbot_TAZ_6'):
			self.RunWizard(self.lulzbotTaz6ToolheadTypePage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()
		if hasattr(e.GetPage(), 'OnPageShown'):
			e.GetPage().OnPageShown()

	def OnCancel(self, e):
		profile.putProfileSetting('nozzle_size', self._nozzle_size)
		profile.putMachineSetting('machine_name', self._machine_name)
		profile.putMachineSetting('machine_type', self._machine_type)
		profile.putMachineSetting('extruder_amount', self._extruder_amount)
		profile.putMachineSetting('toolhead', self._toolhead)
		profile.putMachineSetting('toolhead_shortname', self._toolhead_shortname)
		profile.putMachineSetting('extruder_offset_x1', self._extruder_offset_x1)
		profile.putMachineSetting('extruder_offset_y1', self._extruder_offset_y1)
		profile.putMachineSetting('machine_width', self._machine_width)
		profile.putMachineSetting('machine_height', self._machine_height)

class ConfigWizard(wx.wizard.Wizard):
	def __init__(self, addNew = False):
		super(ConfigWizard, self).__init__(None, -1, _("Configuration Wizard"))

		self._old_machine_index = int(profile.getPreferenceFloat('active_machine'))
		if addNew:
			profile.setActiveMachine(profile.getMachineCount())

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
		self.Bind(wx.wizard.EVT_WIZARD_CANCEL, self.OnCancel)

		self.machineSelectPage = MachineSelectPage(self)
		self.ultimakerSelectParts = SelectParts(self)
		self.ultimakerFirmwareUpgradePage = UltimakerFirmwareUpgradePage(self)
		self.ultimakerCheckupPage = UltimakerCheckupPage(self)
		self.ultimakerCalibrationPage = UltimakerCalibrationPage(self)
		self.ultimakerCalibrateStepsPerEPage = UltimakerCalibrateStepsPerEPage(self)
		self.bedLevelPage = bedLevelWizardMain(self)
		self.headOffsetCalibration = headOffsetCalibrationPage(self)
		self.printrbotSelectType = PrintrbotPage(self)
		self.otherMachineSelectPage = OtherMachineSelectPage(self)
		self.customRepRapInfoPage = CustomRepRapInfoPage(self)
		self.otherMachineInfoPage = OtherMachineInfoPage(self)

		self.ultimaker2ReadyPage = Ultimaker2ReadyPage(self)
		self.lulzbotReadyPage = LulzbotReadyPage(self)
		self.lulzbotFirmwarePage = LulzbotFirmwareUpdatePage(self)
		self.lulzbotMiniToolheadPage = LulzbotMiniToolheadSelectPage(self)
		self.lulzbotTazToolheadPage = LulzbotTazToolheadSelectPage(self)
		self.lulzbotTazToolheadTypePage = LulzbotTazToolheadTypeSelectPage(self)
		self.lulzbotTazHotendPage = LulzbotHotendSelectPage(self)
		self.lulzbotTaz5NozzleSelectPage = LulzbotTaz5NozzleSelectPage(self)
		self.lulzbotMachineSelectPage = LulzbotMachineSelectPage(self)
		self.lulzbotTazBedSelectPage = LulzbotTazBedSelectPage(self)
		self.lulzbotTazSelectPage = LulzbotTazSelectPage(self)
		self.lulzbotTaz6ToolheadPage = LulzbotTaz6ToolheadSelectPage(self)
		self.lulzbotTaz6ToolheadTypePage = LulzbotTaz6ToolheadTypeSelectPage(self)

		wx.wizard.WizardPageSimple.Chain(self.lulzbotMachineSelectPage, self.lulzbotMiniToolheadPage)
		wx.wizard.WizardPageSimple.Chain(self.lulzbotTaz6ToolheadTypePage, self.lulzbotTaz6ToolheadPage)
		wx.wizard.WizardPageSimple.Chain(self.lulzbotTazHotendPage, self.lulzbotTazToolheadPage)
		wx.wizard.WizardPageSimple.Chain(self.machineSelectPage, self.ultimakerSelectParts)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerSelectParts, self.ultimakerFirmwareUpgradePage)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerFirmwareUpgradePage, self.ultimakerCheckupPage)
		wx.wizard.WizardPageSimple.Chain(self.ultimakerCheckupPage, self.bedLevelPage)
		wx.wizard.WizardPageSimple.Chain(self.printrbotSelectType, self.otherMachineInfoPage)
		wx.wizard.WizardPageSimple.Chain(self.otherMachineSelectPage, self.customRepRapInfoPage)

		self.RunWizard(self.lulzbotMachineSelectPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()
		if hasattr(e.GetPage(), 'OnPageShown'):
			e.GetPage().OnPageShown()

	def OnCancel(self, e):
		new_machine_index = int(profile.getPreferenceFloat('active_machine'))
		profile.setActiveMachine(self._old_machine_index)
		profile.removeMachine(new_machine_index)

class bedLevelWizardMain(InfoPage):
	def __init__(self, parent):
		super(bedLevelWizardMain, self).__init__(parent, _("Bed leveling wizard"))

		self.AddText(_('This wizard will help you in leveling your printer bed'))
		self.AddSeperator()
		self.AddText(_('It will do the following steps'))
		self.AddText(_('* Move the printer head to each corner'))
		self.AddText(_('  and let you adjust the height of the bed to the nozzle'))
		self.AddText(_('* Print a line around the bed to check if it is level'))
		self.AddSeperator()

		self.connectButton = self.AddButton(_('Connect to printer'))
		self.comm = None

		self.infoBox = self.AddInfoBox()
		self.resumeButton = self.AddButton(_('Resume'))
		self.upButton, self.downButton = self.AddDualButton(_('Up 0.2mm'), _('Down 0.2mm'))
		self.upButton2, self.downButton2 = self.AddDualButton(_('Up 10mm'), _('Down 10mm'))
		self.resumeButton.Enable(False)

		self.upButton.Enable(False)
		self.downButton.Enable(False)
		self.upButton2.Enable(False)
		self.downButton2.Enable(False)

		self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connectButton)
		self.Bind(wx.EVT_BUTTON, self.OnResume, self.resumeButton)
		self.Bind(wx.EVT_BUTTON, self.OnBedUp, self.upButton)
		self.Bind(wx.EVT_BUTTON, self.OnBedDown, self.downButton)
		self.Bind(wx.EVT_BUTTON, self.OnBedUp2, self.upButton2)
		self.Bind(wx.EVT_BUTTON, self.OnBedDown2, self.downButton2)

	def OnConnect(self, e = None):
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnConnect)
			return
		self.connectButton.Enable(False)
		self.comm = machineCom.MachineCom(callbackObject=self)
		self.infoBox.SetBusy(_('Connecting to machine.'))
		self._wizardState = 0

	def OnBedUp(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z9.8 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def OnBedDown(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z10.2 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def OnBedUp2(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def OnBedDown2(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		self.comm.sendCommand('G92 Z10')
		self.comm.sendCommand('G1 Z20 F%d' % (feedZ))
		self.comm.sendCommand('M400')

	def AllowNext(self):
		if self.GetParent().headOffsetCalibration is not None and int(profile.getMachineSetting('extruder_amount')) > 1:
			wx.wizard.WizardPageSimple.Chain(self, self.GetParent().headOffsetCalibration)
		return True

	def OnResume(self, e):
		feedZ = profile.getProfileSettingFloat('print_speed') * 60
		feedTravel = profile.getProfileSettingFloat('travel_speed') * 60
		if self._wizardState == -1:
			wx.CallAfter(self.infoBox.SetInfo, _('Homing printer...'))
			wx.CallAfter(self.upButton.Enable, False)
			wx.CallAfter(self.downButton.Enable, False)
			wx.CallAfter(self.upButton2.Enable, False)
			wx.CallAfter(self.downButton2.Enable, False)
			self.comm.sendCommand('M105')
			self.comm.sendCommand('G28')
			self._wizardState = 1
		elif self._wizardState == 2:
			if profile.getMachineSetting('has_heated_bed') == 'True':
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to back center...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') / 2.0, profile.getMachineSettingFloat('machine_depth'), feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 3
			else:
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to back left corner...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (0, profile.getMachineSettingFloat('machine_depth'), feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 3
		elif self._wizardState == 4:
			if profile.getMachineSetting('has_heated_bed') == 'True':
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to front right corner...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') - 5.0, 5, feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 7
			else:
				wx.CallAfter(self.infoBox.SetBusy, _('Moving head to back right corner...'))
				self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
				self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') - 5.0, profile.getMachineSettingFloat('machine_depth') - 25, feedTravel))
				self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
				self.comm.sendCommand('M400')
				self._wizardState = 5
		elif self._wizardState == 6:
			wx.CallAfter(self.infoBox.SetBusy, _('Moving head to front right corner...'))
			self.comm.sendCommand('G1 Z3 F%d' % (feedZ))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (profile.getMachineSettingFloat('machine_width') - 5.0, 20, feedTravel))
			self.comm.sendCommand('G1 Z0 F%d' % (feedZ))
			self.comm.sendCommand('M400')
			self._wizardState = 7
		elif self._wizardState == 8:
			wx.CallAfter(self.infoBox.SetBusy, _('Heating up printer...'))
			self.comm.sendCommand('G1 Z15 F%d' % (feedZ))
			self.comm.sendCommand('M104 S%d' % (profile.getProfileSettingFloat('print_temperature')))
			self.comm.sendCommand('G1 X%d Y%d F%d' % (0, 0, feedTravel))
			self._wizardState = 9
		elif self._wizardState == 10:
			self._wizardState = 11
			wx.CallAfter(self.infoBox.SetInfo, _('Printing a square on the printer bed at 0.3mm height.'))
			feedZ = profile.getProfileSettingFloat('print_speed') * 60
			feedPrint = profile.getProfileSettingFloat('print_speed') * 60
			feedTravel = profile.getProfileSettingFloat('travel_speed') * 60
			w = profile.getMachineSettingFloat('machine_width') - 10
			d = profile.getMachineSettingFloat('machine_depth')
			filamentRadius = profile.getProfileSettingFloat('filament_diameter') / 2
			filamentArea = math.pi * filamentRadius * filamentRadius
			ePerMM = (profile.calculateEdgeWidth() * 0.3) / filamentArea
			eValue = 0.0

			gcodeList = [
				'G1 Z2 F%d' % (feedZ),
				'G92 E0',
				'G1 X%d Y%d F%d' % (5, 5, feedTravel),
				'G1 Z0.3 F%d' % (feedZ)]
			eValue += 5.0
			gcodeList.append('G1 E%f F%d' % (eValue, profile.getProfileSettingFloat('retraction_speed') * 60))

			for i in xrange(0, 3):
				dist = 5.0 + 0.4 * float(i)
				eValue += (d - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (dist, d - dist, eValue, feedPrint))
				eValue += (w - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (w - dist, d - dist, eValue, feedPrint))
				eValue += (d - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (w - dist, dist, eValue, feedPrint))
				eValue += (w - 2.0*dist) * ePerMM
				gcodeList.append('G1 X%f Y%f E%f F%d' % (dist, dist, eValue, feedPrint))

			gcodeList.append('M400')
			self.comm.printGCode(gcodeList)
		self.resumeButton.Enable(False)

	def mcLog(self, message):
		print 'Log:', message

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if self._wizardState == 1:
			self._wizardState = 2
			wx.CallAfter(self.infoBox.SetAttention, _('Adjust the front left screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 3:
			self._wizardState = 4
			if profile.getMachineSetting('has_heated_bed') == 'True':
				wx.CallAfter(self.infoBox.SetAttention, _('Adjust the back screw of your printer bed\nSo the nozzle just hits the bed.'))
			else:
				wx.CallAfter(self.infoBox.SetAttention, _('Adjust the back left screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 5:
			self._wizardState = 6
			wx.CallAfter(self.infoBox.SetAttention, _('Adjust the back right screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 7:
			self._wizardState = 8
			wx.CallAfter(self.infoBox.SetAttention, _('Adjust the front right screw of your printer bed\nSo the nozzle just hits the bed.'))
			wx.CallAfter(self.resumeButton.Enable, True)
		elif self._wizardState == 9:
			if temp[0] < profile.getProfileSettingFloat('print_temperature') - 5:
				wx.CallAfter(self.infoBox.SetInfo, _('Heating up printer: %d/%d') % (temp[0], profile.getProfileSettingFloat('print_temperature')))
			else:
				wx.CallAfter(self.infoBox.SetAttention, _('The printer is hot now. Please insert some PLA filament into the printer.'))
				wx.CallAfter(self.resumeButton.Enable, True)
				self._wizardState = 10

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			if self._wizardState == 0:
				wx.CallAfter(self.infoBox.SetAttention, _('Use the up/down buttons to move the bed and adjust your Z endstop.'))
				wx.CallAfter(self.upButton.Enable, True)
				wx.CallAfter(self.downButton.Enable, True)
				wx.CallAfter(self.upButton2.Enable, True)
				wx.CallAfter(self.downButton2.Enable, True)
				wx.CallAfter(self.resumeButton.Enable, True)
				self._wizardState = -1
			elif self._wizardState == 11 and not self.comm.isPrinting():
				self.comm.sendCommand('G1 Z15 F%d' % (profile.getProfileSettingFloat('print_speed') * 60))
				self.comm.sendCommand('G92 E0')
				self.comm.sendCommand('G1 E-10 F%d' % (profile.getProfileSettingFloat('retraction_speed') * 60))
				self.comm.sendCommand('M104 S0')
				wx.CallAfter(self.infoBox.SetInfo, _('Calibration finished.\nThe squares on the bed should slightly touch each other.'))
				wx.CallAfter(self.infoBox.SetReadyIndicator)
				wx.CallAfter(self.GetParent().FindWindowById(wx.ID_FORWARD).Enable)
				wx.CallAfter(self.connectButton.Enable, True)
				self._wizardState = 12
		elif self.comm.isError():
			wx.CallAfter(self.infoBox.SetError, _('Failed to establish connection with the printer.'), 'http://wiki.ultimaker.com/Cura:_Connection_problems')

	def mcMessage(self, message):
		pass

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass

class headOffsetCalibrationPage(InfoPage):
	def __init__(self, parent):
		super(headOffsetCalibrationPage, self).__init__(parent, _("Printer head offset calibration"))

		self.AddText(_('This wizard will help you in calibrating the printer head offsets of your dual extrusion machine'))
		self.AddSeperator()

		self.connectButton = self.AddButton(_('Connect to printer'))
		self.comm = None

		self.infoBox = self.AddInfoBox()
		self.textEntry = self.AddTextCtrl('')
		self.textEntry.Enable(False)
		self.resumeButton = self.AddButton(_('Resume'))
		self.resumeButton.Enable(False)

		self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connectButton)
		self.Bind(wx.EVT_BUTTON, self.OnResume, self.resumeButton)

	def AllowBack(self):
		return True

	def OnConnect(self, e = None):
		if self.comm is not None:
			self.comm.close()
			del self.comm
			self.comm = None
			wx.CallAfter(self.OnConnect)
			return
		self.connectButton.Enable(False)
		self.comm = machineCom.MachineCom(callbackObject=self)
		self.infoBox.SetBusy(_('Connecting to machine.'))
		self._wizardState = 0

	def OnResume(self, e):
		if self._wizardState == 2:
			self._wizardState = 3
			wx.CallAfter(self.infoBox.SetBusy, _('Printing initial calibration cross'))

			w = profile.getMachineSettingFloat('machine_width')
			d = profile.getMachineSettingFloat('machine_depth')

			gcode = gcodeGenerator.gcodeGenerator()
			gcode.setExtrusionRate(profile.getProfileSettingFloat('nozzle_size') * 1.5, 0.2)
			gcode.setPrintSpeed(profile.getProfileSettingFloat('bottom_layer_speed'))
			gcode.addCmd('T0')
			gcode.addPrime(15)
			gcode.addCmd('T1')
			gcode.addPrime(15)

			gcode.addCmd('T0')
			gcode.addMove(w/2, 5)
			gcode.addMove(z=0.2)
			gcode.addPrime()
			gcode.addExtrude(w/2, d-5.0)
			gcode.addRetract()
			gcode.addMove(5, d/2)
			gcode.addPrime()
			gcode.addExtrude(w-5.0, d/2)
			gcode.addRetract(15)

			gcode.addCmd('T1')
			gcode.addMove(w/2, 5)
			gcode.addPrime()
			gcode.addExtrude(w/2, d-5.0)
			gcode.addRetract()
			gcode.addMove(5, d/2)
			gcode.addPrime()
			gcode.addExtrude(w-5.0, d/2)
			gcode.addRetract(15)
			gcode.addCmd('T0')

			gcode.addMove(z=25)
			gcode.addMove(0, 0)
			gcode.addCmd('M400')

			self.comm.printGCode(gcode.list())
			self.resumeButton.Enable(False)
		elif self._wizardState == 4:
			try:
				float(self.textEntry.GetValue())
			except ValueError:
				return
			profile.putPreference('extruder_offset_x1', self.textEntry.GetValue())
			self._wizardState = 5
			self.infoBox.SetAttention(_('Please measure the distance between the horizontal lines in millimeters.'))
			self.textEntry.SetValue('0.0')
			self.textEntry.Enable(True)
		elif self._wizardState == 5:
			try:
				float(self.textEntry.GetValue())
			except ValueError:
				return
			profile.putPreference('extruder_offset_y1', self.textEntry.GetValue())
			self._wizardState = 6
			self.infoBox.SetBusy(_('Printing the fine calibration lines.'))
			self.textEntry.SetValue('')
			self.textEntry.Enable(False)
			self.resumeButton.Enable(False)

			x = profile.getMachineSettingFloat('extruder_offset_x1')
			y = profile.getMachineSettingFloat('extruder_offset_y1')
			gcode = gcodeGenerator.gcodeGenerator()
			gcode.setExtrusionRate(profile.getProfileSettingFloat('nozzle_size') * 1.5, 0.2)
			gcode.setPrintSpeed(25)
			gcode.addHome()
			gcode.addCmd('T0')
			gcode.addMove(50, 40, 0.2)
			gcode.addPrime(15)
			for n in xrange(0, 10):
				gcode.addExtrude(50 + n * 10, 150)
				gcode.addExtrude(50 + n * 10 + 5, 150)
				gcode.addExtrude(50 + n * 10 + 5, 40)
				gcode.addExtrude(50 + n * 10 + 10, 40)
			gcode.addMove(40, 50)
			for n in xrange(0, 10):
				gcode.addExtrude(150, 50 + n * 10)
				gcode.addExtrude(150, 50 + n * 10 + 5)
				gcode.addExtrude(40, 50 + n * 10 + 5)
				gcode.addExtrude(40, 50 + n * 10 + 10)
			gcode.addRetract(15)

			gcode.addCmd('T1')
			gcode.addMove(50 - x, 30 - y, 0.2)
			gcode.addPrime(15)
			for n in xrange(0, 10):
				gcode.addExtrude(50 + n * 10.2 - 1.0 - x, 140 - y)
				gcode.addExtrude(50 + n * 10.2 - 1.0 + 5.1 - x, 140 - y)
				gcode.addExtrude(50 + n * 10.2 - 1.0 + 5.1 - x, 30 - y)
				gcode.addExtrude(50 + n * 10.2 - 1.0 + 10 - x, 30 - y)
			gcode.addMove(30 - x, 50 - y, 0.2)
			for n in xrange(0, 10):
				gcode.addExtrude(160 - x, 50 + n * 10.2 - 1.0 - y)
				gcode.addExtrude(160 - x, 50 + n * 10.2 - 1.0 + 5.1 - y)
				gcode.addExtrude(30 - x, 50 + n * 10.2 - 1.0 + 5.1 - y)
				gcode.addExtrude(30 - x, 50 + n * 10.2 - 1.0 + 10 - y)
			gcode.addRetract(15)
			gcode.addMove(z=15)
			gcode.addCmd('M400')
			gcode.addCmd('M104 T0 S0')
			gcode.addCmd('M104 T1 S0')
			self.comm.printGCode(gcode.list())
		elif self._wizardState == 7:
			try:
				n = int(self.textEntry.GetValue()) - 1
			except:
				return
			x = profile.getMachineSettingFloat('extruder_offset_x1')
			x += -1.0 + n * 0.1
			profile.putPreference('extruder_offset_x1', '%0.2f' % (x))
			self.infoBox.SetAttention(_('Which horizontal line number lays perfect on top of each other? Front most line is zero.'))
			self.textEntry.SetValue('10')
			self._wizardState = 8
		elif self._wizardState == 8:
			try:
				n = int(self.textEntry.GetValue()) - 1
			except:
				return
			y = profile.getMachineSettingFloat('extruder_offset_y1')
			y += -1.0 + n * 0.1
			profile.putPreference('extruder_offset_y1', '%0.2f' % (y))
			self.infoBox.SetInfo(_('Calibration finished. Offsets are: %s %s') % (profile.getMachineSettingFloat('extruder_offset_x1'), profile.getMachineSettingFloat('extruder_offset_y1')))
			self.infoBox.SetReadyIndicator()
			self._wizardState = 8
			self.comm.close()
			self.resumeButton.Enable(False)

	def mcLog(self, message):
		print 'Log:', message

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		if self._wizardState == 1:
			if temp[0] >= 210 and temp[1] >= 210:
				self._wizardState = 2
				wx.CallAfter(self.infoBox.SetAttention, _('Please load both extruders with PLA.'))
				wx.CallAfter(self.resumeButton.Enable, True)
				wx.CallAfter(self.resumeButton.SetFocus)

	def mcStateChange(self, state):
		if self.comm is None:
			return
		if self.comm.isOperational():
			if self._wizardState == 0:
				wx.CallAfter(self.infoBox.SetInfo, _('Homing printer and heating up both extruders.'))
				self.comm.sendCommand('M105')
				self.comm.sendCommand('M104 S220 T0')
				self.comm.sendCommand('M104 S220 T1')
				self.comm.sendCommand('G28')
				self.comm.sendCommand('G1 Z15 F%d' % (profile.getProfileSettingFloat('print_speed') * 60))
				self._wizardState = 1
			if not self.comm.isPrinting():
				if self._wizardState == 3:
					self._wizardState = 4
					wx.CallAfter(self.infoBox.SetAttention, _('Please measure the distance between the vertical lines in millimeters.'))
					wx.CallAfter(self.textEntry.SetValue, '0.0')
					wx.CallAfter(self.textEntry.Enable, True)
					wx.CallAfter(self.resumeButton.Enable, True)
					wx.CallAfter(self.resumeButton.SetFocus)
				elif self._wizardState == 6:
					self._wizardState = 7
					wx.CallAfter(self.infoBox.SetAttention, _('Which vertical line number lays perfect on top of each other? Leftmost line is zero.'))
					wx.CallAfter(self.textEntry.SetValue, '10')
					wx.CallAfter(self.textEntry.Enable, True)
					wx.CallAfter(self.resumeButton.Enable, True)
					wx.CallAfter(self.resumeButton.SetFocus)

		elif self.comm.isError():
			wx.CallAfter(self.infoBox.SetError, _('Failed to establish connection with the printer.'), 'http://wiki.ultimaker.com/Cura:_Connection_problems')

	def mcMessage(self, message):
		pass

	def mcProgress(self, lineNr):
		pass

	def mcZChange(self, newZ):
		pass

class bedLevelWizard(wx.wizard.Wizard):
	def __init__(self):
		super(bedLevelWizard, self).__init__(None, -1, _("Bed leveling wizard"))

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.mainPage = bedLevelWizardMain(self)
		self.headOffsetCalibration = None

		self.RunWizard(self.mainPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()

class headOffsetWizard(wx.wizard.Wizard):
	def __init__(self):
		super(headOffsetWizard, self).__init__(None, -1, _("Head offset wizard"))

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.OnPageChanged)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

		self.mainPage = headOffsetCalibrationPage(self)

		self.RunWizard(self.mainPage)
		self.Destroy()

	def OnPageChanging(self, e):
		e.GetPage().StoreData()

	def OnPageChanged(self, e):
		if e.GetPage().AllowNext():
			self.FindWindowById(wx.ID_FORWARD).Enable()
		else:
			self.FindWindowById(wx.ID_FORWARD).Disable()
		if e.GetPage().AllowBack():
			self.FindWindowById(wx.ID_BACKWARD).Enable()
		else:
			self.FindWindowById(wx.ID_BACKWARD).Disable()
