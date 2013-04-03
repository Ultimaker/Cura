import subprocess
import time
import numpy
import os
import warnings
import threading
import traceback

from Cura.util import profile

def getEngineFilename():
	if os.path.exists('C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'):
		return 'C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'
	return 'SteamEngine'

def getTempFilename():
	warnings.simplefilter('ignore')
	ret = os.tempnam(None, "Cura_Tmp")
	warnings.simplefilter('default')
	return ret

class Slicer(object):
	def __init__(self, progressCallback):
		self._process = None
		self._thread = None
		self._callback = progressCallback
		self._binaryStorageFilename = getTempFilename()
		self._exportFilename = getTempFilename()
		self._progressSteps = ['inset', 'skin', 'export']

	def abortSlicer(self):
		if self._process is not None:
			self._process.terminate()
			self._thread.join()

	def getGCodeFilename(self):
		return self._exportFilename

	def runSlicer(self, scene):
		self.abortSlicer()
		self._callback(0.0, False)

		commandList = [getEngineFilename(), '-vv']
		for k, v in self._engineSettings().iteritems():
			commandList += ['-s', '%s=%s' % (k, str(v))]
		commandList += ['-o', self._exportFilename]
		commandList += ['-b', self._binaryStorageFilename]
		self._objCount = 0
		with open(self._binaryStorageFilename, "wb") as f:
			for obj in scene._objectList:
				if not scene.checkPlatform(obj):
					continue
				for mesh in obj._meshList:
					n = numpy.array(mesh.vertexCount, numpy.int32)
					f.write(n.tostring())
					f.write(mesh.vertexes.tostring())
				pos = obj.getPosition() * 1000
				pos += numpy.array([profile.getPreferenceFloat('machine_width') * 1000 / 2, profile.getPreferenceFloat('machine_depth') * 1000 / 2])
				commandList += ['-m', ','.join(map(str, obj._matrix.getA().flatten()))]
				commandList += ['-s', 'posx=%d' % int(pos[0]), '-s', 'posy=%d' % int(pos[1]), '#']
				self._objCount += 1
		if self._objCount > 0:
			print ' '.join(commandList)
			try:
				self._process = self._runSliceProcess(commandList)
				self._thread = threading.Thread(target=self._watchProcess)
				self._thread.daemon = True
				self._thread.start()
			except OSError:
				traceback.print_exc()

	def _watchProcess(self):
		self._callback(0.0, False)
		line = self._process.stdout.readline()
		while len(line):
			line = line.strip()
			if line.startswith('Progress:'):
				line = line.split(':')
				progressValue = float(line[2]) / float(line[3])
				progressValue /= len(self._progressSteps)
				progressValue += 1.0 / len(self._progressSteps) * self._progressSteps.index(line[1])
				self._callback(progressValue, False)
			else:
				print '#', line.strip()
			line = self._process.stdout.readline()
		for line in self._process.stderr:
			print line.strip()
		returnCode = self._process.wait()
		print returnCode
		if returnCode == 0:
			self._callback(1.0, True)
		else:
			self._callback(0.0, False)
		self._process = None

	def _engineSettings(self):
		return {
			'layerThickness': int(profile.getProfileSettingFloat('layer_height') * 1000),
			'initialLayerThickness': int(profile.getProfileSettingFloat('bottom_thickness') * 1000),
			'filamentDiameter': int(profile.getProfileSettingFloat('filament_diameter') * 1000),
			'extrusionWidth': int(profile.calculateEdgeWidth() * 1000),
			'insetCount': int(profile.calculateLineCount()),
			'downSkinCount': int(profile.calculateSolidLayerCount()),
			'upSkinCount': int(profile.calculateSolidLayerCount()),
			'sparseInfillLineDistance': int(100 * profile.calculateEdgeWidth() * 1000 / profile.getProfileSettingFloat('fill_density')),
			'skirtDistance': int(profile.getProfileSettingFloat('skirt_gap') * 1000),
			'skirtLineCount': int(profile.getProfileSettingFloat('skirt_line_count')),
			'initialSpeedupLayers': int(4),
			'initialLayerSpeed': int(profile.getProfileSettingFloat('bottom_layer_speed')),
			'printSpeed': int(profile.getProfileSettingFloat('print_speed')),
			'moveSpeed': int(profile.getProfileSettingFloat('travel_speed')),
			'fanOnLayerNr': int(profile.getProfileSettingFloat('fan_layer')),
			'supportAngle': int(-1) if profile.getProfileSetting('support') == 'None' else int(60),
			'supportEverywhere': int(1) if profile.getProfileSetting('support') == 'Everywhere' else int(0),
			'retractionAmount': int(profile.getProfileSettingFloat('retraction_amount') * 1000),
			'retractionSpeed': int(profile.getProfileSettingFloat('retraction_speed')),
			'objectSink': int(profile.getProfileSettingFloat('object_sink') * 1000),
		}

	def _runSliceProcess(self, cmdList):
		kwargs = {}
		if subprocess.mswindows:
			su = subprocess.STARTUPINFO()
			su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			su.wShowWindow = subprocess.SW_HIDE
			kwargs['startupinfo'] = su
			kwargs['creationflags'] = 0x00004000 #BELOW_NORMAL_PRIORITY_CLASS
		return subprocess.Popen(cmdList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
