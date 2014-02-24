__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import os
import glob
import subprocess
import platform

import wx

from Cura.util import profile
from Cura.util.resources import getPathForImage

try:
	#Try to find the OpenCV library for video capture.
	from opencv import cv
	from opencv import highgui
except:
	cv = None

try:
	#Use the vidcap library directly from the VideoCapture package. (Windows only)
	#	http://videocapture.sourceforge.net/
	# We're using the binary interface, not the python interface, so we don't depend on PIL
	import vidcap as win32vidcap
except:
	win32vidcap = None

def hasWebcamSupport():
	if cv is None and win32vidcap is None:
		return False
	if not os.path.exists(getFFMPEGpath()):
		return False
	return True


def getFFMPEGpath():
	if platform.system() == "Windows":
		return os.path.normpath(os.path.join(os.path.split(__file__)[0], "../../ffmpeg.exe"))
	elif os.path.exists('/usr/bin/ffmpeg'):
		return '/usr/bin/ffmpeg'
	return os.path.normpath(os.path.join(os.path.split(__file__)[0], "../../ffmpeg"))


class webcam(object):
	def __init__(self):
		self._cam = None
		self._cameraList = None
		self._activeId = -1
		self._overlayImage = wx.Bitmap(getPathForImage('cura-overlay.png'))
		self._overlayUltimaker = wx.Bitmap(getPathForImage('ultimaker-overlay.png'))
		self._doTimelapse = False
		self._bitmap = None

		#open the camera and close it to check if we have a camera, then open the camera again when we use it for the
		# first time.
		cameraList = []
		tryNext = True
		self._camId = 0
		while tryNext:
			tryNext = False
			self._openCam()
			if self._cam is not None:
				cameraList.append(self._cam.getdisplayname())
				tryNext = True
				del self._cam
				self._cam = None
				self._camId += 1
		self._camId = 0
		self._activeId = -1
		self._cameraList = cameraList

	def hasCamera(self):
		return len(self._cameraList) > 0

	def listCameras(self):
		return self._cameraList

	def setActiveCamera(self, cameraIdx):
		self._camId = cameraIdx

	def _openCam(self):
		if self._cameraList is not None and self._camId >= len(self._cameraList):
			return False
		if self._cam is not None:
			if self._activeId != self._camId:
				del self._cam
				self._cam = None
			else:
				return True

		self._activeId = self._camId
		if cv is not None:
			self._cam = highgui.cvCreateCameraCapture(self._camId)
		elif win32vidcap is not None:
			try:
				self._cam = win32vidcap.new_Dev(self._camId, False)
			except:
				pass
		return self._cam is not None

	def propertyPages(self):
		if cv is not None:
			#TODO Make an OpenCV property page
			return []
		elif win32vidcap is not None:
			return ['Image properties', 'Format properties']

	def openPropertyPage(self, pageType=0):
		if not self._openCam():
			return
		if cv is not None:
			pass
		elif win32vidcap is not None:
			if pageType == 0:
				self._cam.displaycapturefilterproperties()
			else:
				del self._cam
				self._cam = None
				tmp = win32vidcap.new_Dev(0, False)
				tmp.displaycapturepinproperties()
				self._cam = tmp

	def takeNewImage(self, withOverlay = True):
		if not self._openCam():
			return
		if cv is not None:
			frame = cv.QueryFrame(self._cam)
			cv.CvtColor(frame, frame, cv.CV_BGR2RGB)
			bitmap = wx.BitmapFromBuffer(frame.width, frame.height, frame.imageData)
		elif win32vidcap is not None:
			buffer, width, height = self._cam.getbuffer()
			try:
				wxImage = wx.EmptyImage(width, height)
				wxImage.SetData(buffer[::-1])
				wxImage = wxImage.Mirror()
				if self._bitmap is not None:
					del self._bitmap
				bitmap = wxImage.ConvertToBitmap()
				del wxImage
				del buffer
			except:
				pass

		if withOverlay:
			dc = wx.MemoryDC()
			dc.SelectObject(bitmap)
			dc.DrawBitmap(self._overlayImage, bitmap.GetWidth() - self._overlayImage.GetWidth() - 5, 5, True)
			if profile.getMachineSetting('machine_type').startswith('ultimaker'):
				dc.DrawBitmap(self._overlayUltimaker, (bitmap.GetWidth() - self._overlayUltimaker.GetWidth()) / 2,
					bitmap.GetHeight() - self._overlayUltimaker.GetHeight() - 5, True)
			dc.SelectObject(wx.NullBitmap)

		self._bitmap = bitmap

		if self._doTimelapse:
			filename = os.path.normpath(os.path.join(os.path.split(__file__)[0], "../__tmp_snap",
				"__tmp_snap_%04d.jpg" % (self._snapshotCount)))
			self._snapshotCount += 1
			bitmap.SaveFile(filename, wx.BITMAP_TYPE_JPEG)

		return self._bitmap

	def getLastImage(self):
		return self._bitmap

	def startTimelapse(self, filename):
		if not self._openCam():
			return
		self._cleanTempDir()
		self._timelapseFilename = filename
		self._snapshotCount = 0
		self._doTimelapse = True
		print "startTimelapse"

	def endTimelapse(self):
		if self._doTimelapse:
			ffmpeg = getFFMPEGpath()
			basePath = os.path.normpath(
				os.path.join(os.path.split(__file__)[0], "../__tmp_snap", "__tmp_snap_%04d.jpg"))
			subprocess.call(
				[ffmpeg, '-r', '12.5', '-i', basePath, '-vcodec', 'mpeg2video', '-pix_fmt', 'yuv420p', '-r', '25', '-y',
				 '-b:v', '1500k', '-f', 'vob', self._timelapseFilename])
		self._doTimelapse = False

	def _cleanTempDir(self):
		basePath = os.path.normpath(os.path.join(os.path.split(__file__)[0], "../__tmp_snap"))
		try:
			os.makedirs(basePath)
		except:
			pass
		for filename in glob.iglob(basePath + "/*.jpg"):
			os.remove(filename)
