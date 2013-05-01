import subprocess
import time
import math
import numpy
import os
import warnings
import threading
import traceback
import platform
import sys

from Cura.util import profile

def getEngineFilename():
	if platform.system() == 'Windows':
		if os.path.exists('C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'):
			return 'C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'
		return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'SteamEngine.exe'))
	if hasattr(sys, 'frozen'):
		return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..', 'SteamEngine'))
	return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'SteamEngine'))

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
		self._objCount = 0
		self._sliceLog = []
		self._printTimeSeconds = None
		self._filamentMM = None

	def cleanup(self):
		self.abortSlicer()
		try:
			os.remove(self._binaryStorageFilename)
		except:
			pass
		try:
			os.remove(self._exportFilename)
		except:
			pass

	def abortSlicer(self):
		if self._process is not None:
			try:
				self._process.terminate()
			except:
				pass
			self._thread.join()

	def getGCodeFilename(self):
		return self._exportFilename

	def getSliceLog(self):
		return self._sliceLog

	def getFilamentWeight(self):
		#Calculates the weight of the filament in kg
		radius = float(profile.getProfileSetting('filament_diameter')) / 2
		volumeM3 = (self._filamentMM * (math.pi * radius * radius)) / (1000*1000*1000)
		return volumeM3 * profile.getPreferenceFloat('filament_physical_density')

	def getFilamentCost(self):
		cost_kg = profile.getPreferenceFloat('filament_cost_kg')
		cost_meter = profile.getPreferenceFloat('filament_cost_meter')
		if cost_kg > 0.0 and cost_meter > 0.0:
			return "%.2f / %.2f" % (self.getFilamentWeight() * cost_kg, self._filamentMM / 1000.0 * cost_meter)
		elif cost_kg > 0.0:
			return "%.2f" % (self.getFilamentWeight() * cost_kg)
		elif cost_meter > 0.0:
			return "%.2f" % (self._filamentMM / 1000.0 * cost_meter)
		return None

	def getPrintTime(self):
		return '%02d:%02d' % (int(self._printTimeSeconds / 60 / 60), int(self._printTimeSeconds / 60) % 60)

	def getFilamentAmount(self):
		return '%0.2fm %0.0fgram' % (float(self._filamentMM) / 1000.0, self.getFilamentWeight() * 1000.0)

	def runSlicer(self, scene):
		self.abortSlicer()
		self._callback(-1.0, False)

		commandList = [getEngineFilename(), '-vv']
		for k, v in self._engineSettings().iteritems():
			commandList += ['-s', '%s=%s' % (k, str(v))]
		commandList += ['-o', self._exportFilename]
		commandList += ['-b', self._binaryStorageFilename]
		self._objCount = 0
		with open(self._binaryStorageFilename, "wb") as f:
			order = scene.printOrder()
			if order is None:
				pos = numpy.array([profile.getPreferenceFloat('machine_width') * 1000 / 2, profile.getPreferenceFloat('machine_depth') * 1000 / 2])
				commandList += ['-s', 'posx=%d' % int(pos[0]), '-s', 'posy=%d' % int(pos[1])]

				vertexTotal = 0
				for obj in scene.objects():
					if scene.checkPlatform(obj):
						for mesh in obj._meshList:
							vertexTotal += mesh.vertexCount

				f.write(numpy.array([vertexTotal], numpy.int32).tostring())
				for obj in scene.objects():
					if scene.checkPlatform(obj):
						for mesh in obj._meshList:
							vertexes = (numpy.matrix(mesh.vertexes, copy = False) * numpy.matrix(obj._matrix, numpy.float32)).getA()
							vertexes -= obj._drawOffset
							vertexes += numpy.array([obj.getPosition()[0], obj.getPosition()[1], 0.0])
							f.write(vertexes.tostring())

				commandList += ['#']
				self._objCount = 1
			else:
				for n in order:
					obj = scene.objects()[n]
					for mesh in obj._meshList:
						f.write(numpy.array([mesh.vertexCount], numpy.int32).tostring())
						f.write(mesh.vertexes.tostring())
					pos = obj.getPosition() * 1000
					pos += numpy.array([profile.getPreferenceFloat('machine_width') * 1000 / 2, profile.getPreferenceFloat('machine_depth') * 1000 / 2])
					commandList += ['-m', ','.join(map(str, obj._matrix.getA().flatten()))]
					commandList += ['-s', 'posx=%d' % int(pos[0]), '-s', 'posy=%d' % int(pos[1])]
					commandList += ['#' * len(obj._meshList)]
					self._objCount += 1
		if self._objCount > 0:
			try:
				self._process = self._runSliceProcess(commandList)
				self._thread = threading.Thread(target=self._watchProcess)
				self._thread.daemon = True
				self._thread.start()
			except OSError:
				traceback.print_exc()

	def _watchProcess(self):
		self._callback(0.0, False)
		self._sliceLog = []
		self._printTimeSeconds = None
		self._filamentMM = None

		line = self._process.stdout.readline()
		objectNr = 0
		while len(line):
			line = line.strip()
			if line.startswith('Progress:'):
				line = line.split(':')
				if line[1] == 'process':
					objectNr += 1
				elif line[1] in self._progressSteps:
					progressValue = float(line[2]) / float(line[3])
					progressValue /= len(self._progressSteps)
					progressValue += 1.0 / len(self._progressSteps) * self._progressSteps.index(line[1])

					progressValue /= self._objCount
					progressValue += 1.0 / self._objCount * objectNr
					try:
						self._callback(progressValue, False)
					except:
						pass
			elif line.startswith('Print time:'):
				self._printTimeSeconds = int(line.split(':')[1].strip())
			elif line.startswith('Filament:'):
				self._filamentMM = int(line.split(':')[1].strip())
			else:
				self._sliceLog.append(line.strip())
			line = self._process.stdout.readline()
		for line in self._process.stderr:
			self._sliceLog.append(line.strip())
		returnCode = self._process.wait()
		try:
			if returnCode == 0:
				self._callback(1.0, True)
			else:
				self._callback(-1.0, False)
		except:
			pass
		self._process = None

	def _engineSettings(self):
		return {
			'layerThickness': int(profile.getProfileSettingFloat('layer_height') * 1000),
			'initialLayerThickness': int(profile.getProfileSettingFloat('bottom_thickness') * 1000) if profile.getProfileSettingFloat('bottom_thickness') > 0.0 else int(profile.getProfileSettingFloat('layer_height') * 1000),
			'filamentDiameter': int(profile.getProfileSettingFloat('filament_diameter') * 1000),
			'filamentFlow': int(profile.getProfileSettingFloat('filament_flow')),
			'extrusionWidth': int(profile.calculateEdgeWidth() * 1000),
			'insetCount': int(profile.calculateLineCount()),
			'downSkinCount': int(profile.calculateSolidLayerCount()) if profile.getProfileSetting('solid_bottom') == 'True' else 0,
			'upSkinCount': int(profile.calculateSolidLayerCount()) if profile.getProfileSetting('solid_top') == 'True' else 0,
			'sparseInfillLineDistance': int(100 * profile.calculateEdgeWidth() * 1000 / profile.getProfileSettingFloat('fill_density')) if profile.getProfileSettingFloat('fill_density') > 0 else 9999999999,
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
			'minimalLayerTime': int(profile.getProfileSettingFloat('cool_min_layer_time')),
			'minimalFeedrate': int(profile.getProfileSettingFloat('cool_min_feedrate')),
			'coolHeadLift': 1 if profile.getProfileSetting('cool_head_lift') == 'True' else 0,
			'startCode': profile.getAlterationFileContents('start.gcode'),
			'endCode': profile.getAlterationFileContents('end.gcode'),
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
