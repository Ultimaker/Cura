from __future__ import absolute_import
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import sys
import os
import platform
import shutil
import glob
import warnings

#Only import the _core to save import time
import wx._core


class CuraApp(wx.App):
	def __init__(self, files):
		if platform.system() == "Windows" and not 'PYCHARM_HOSTED' in os.environ:
			super(CuraApp, self).__init__(redirect=True, filename='output.txt')
		else:
			super(CuraApp, self).__init__(redirect=False)

		self.mainWindow = None
		self.splash = None
		self.loadFiles = files

		if sys.platform.startswith('darwin'):
			#Do not show a splashscreen on OSX, as by Apple guidelines
			self.afterSplashCallback()
		else:
			from Cura.gui import splashScreen
			self.splash = splashScreen.splashScreen(self.afterSplashCallback)

	def MacOpenFile(self, path):
		try:
			self.mainWindow.OnDropFiles([path])
		except Exception as e:
			warnings.warn("File at {p} cannot be read: {e}".format(p=path, e=str(e)))

	def afterSplashCallback(self):
		#These imports take most of the time and thus should be done after showing the splashscreen
		import webbrowser
		from Cura.gui import mainWindow
		from Cura.gui import configWizard
		from Cura.util import profile
		from Cura.util import resources
		from Cura.util import version

		resources.setupLocalization()  # it's important to set up localization at very beginning to install _

		#If we do not have preferences yet, try to load it from a previous Cura install
		if profile.getMachineSetting('machine_type') == 'unknown':
			try:
				otherCuraInstalls = profile.getAlternativeBasePaths()
				otherCuraInstalls.sort()
				if len(otherCuraInstalls) > 0:
					profile.loadPreferences(os.path.join(otherCuraInstalls[-1], 'preferences.ini'))
					profile.loadProfile(os.path.join(otherCuraInstalls[-1], 'current_profile.ini'))
			except:
				import traceback
				print traceback.print_exc()

		#If we haven't run it before, run the configuration wizard.
		if profile.getMachineSetting('machine_type') == 'unknown':
			if platform.system() == "Windows":
				exampleFile = os.path.normpath(os.path.join(resources.resourceBasePath, 'example', 'UltimakerRobot_support.stl'))
			else:
				#Check if we need to copy our examples
				exampleFile = os.path.expanduser('~/CuraExamples/UltimakerRobot_support.stl')
				if not os.path.isfile(exampleFile):
					try:
						os.makedirs(os.path.dirname(exampleFile))
					except:
						pass
					for filename in glob.glob(os.path.normpath(os.path.join(resources.resourceBasePath, 'example', '*.*'))):
						shutil.copy(filename, os.path.join(os.path.dirname(exampleFile), os.path.basename(filename)))
			self.loadFiles = [exampleFile]
			if self.splash is not None:
				self.splash.Show(False)
			configWizard.configWizard()

		if profile.getPreference('check_for_updates') == 'True':
			newVersion = version.checkForNewerVersion()
			if newVersion is not None:
				if self.splash is not None:
					self.splash.Show(False)
				if wx.MessageBox(_("A new version of Cura is available, would you like to download?"), _("New version available"), wx.YES_NO | wx.ICON_INFORMATION) == wx.YES:
					webbrowser.open(newVersion)
					return
		self.mainWindow = mainWindow.mainWindow()
		if self.splash is not None:
			self.splash.Show(False)
		self.mainWindow.Show()
		self.mainWindow.OnDropFiles(self.loadFiles)

		setFullScreenCapable(self.mainWindow)

if platform.system() == "Darwin":
	try:
		import ctypes, objc
		_objc = ctypes.PyDLL(objc._objc.__file__)

		# PyObject *PyObjCObject_New(id objc_object, int flags, int retain)
		_objc.PyObjCObject_New.restype = ctypes.py_object
		_objc.PyObjCObject_New.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

		def setFullScreenCapable(frame):
			frameobj = _objc.PyObjCObject_New(frame.GetHandle(), 0, 1)

			NSWindowCollectionBehaviorFullScreenPrimary = 1 << 7
			window = frameobj.window()
			newBehavior = window.collectionBehavior() | NSWindowCollectionBehaviorFullScreenPrimary
			window.setCollectionBehavior_(newBehavior)
	except:
		def setFullScreenCapable(frame):
			pass

else:
	def setFullScreenCapable(frame):
		pass
