__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
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
import urllib
import urllib2
import hashlib

from Cura.util import profile
from Cura.util import version

def getEngineFilename():
	if platform.system() == 'Windows':
		if os.path.exists('C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'):
			return 'C:/Software/Cura_SteamEngine/_bin/Release/Cura_SteamEngine.exe'
		return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'CuraEngine.exe'))
	if hasattr(sys, 'frozen'):
		return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..', 'CuraEngine'))
	if os.path.isfile('/usr/bin/CuraEngine'):
		return '/usr/bin/CuraEngine'
	if os.path.isfile('/usr/local/bin/CuraEngine'):
		return '/usr/local/bin/CuraEngine'
	return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'CuraEngine'))

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
		self._modelHash = None
		self._id = 0

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
		self._thread = None

	def wait(self):
		if self._thread is not None:
			self._thread.join()

	def getGCodeFilename(self):
		return self._exportFilename

	def getSliceLog(self):
		return self._sliceLog

	def getID(self):
		return self._id

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
		if int(self._printTimeSeconds / 60 / 60) < 1:
			return '%d minutes' % (int(self._printTimeSeconds / 60) % 60)
		if int(self._printTimeSeconds / 60 / 60) == 1:
			return '%d hour %d minutes' % (int(self._printTimeSeconds / 60 / 60), int(self._printTimeSeconds / 60) % 60)
		return '%d hours %d minutes' % (int(self._printTimeSeconds / 60 / 60), int(self._printTimeSeconds / 60) % 60)

	def getFilamentAmount(self):
		return '%0.2f meter %0.0f gram' % (float(self._filamentMM) / 1000.0, self.getFilamentWeight() * 1000.0)

	def runSlicer(self, scene):
		extruderCount = 1
		for obj in scene.objects():
			if scene.checkPlatform(obj):
				extruderCount = max(extruderCount, len(obj._meshList))

		commandList = [getEngineFilename(), '-vv']
		for k, v in self._engineSettings(extruderCount).iteritems():
			commandList += ['-s', '%s=%s' % (k, str(v))]
		commandList += ['-o', self._exportFilename]
		commandList += ['-b', self._binaryStorageFilename]
		self._objCount = 0
		with open(self._binaryStorageFilename, "wb") as f:
			hash = hashlib.sha512()
			order = scene.printOrder()
			if order is None:
				pos = numpy.array(profile.getMachineCenterCoords()) * 1000
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
							hash.update(mesh.vertexes.tostring())

				commandList += ['#']
				self._objCount = 1
			else:
				for n in order:
					obj = scene.objects()[n]
					for mesh in obj._meshList:
						f.write(numpy.array([mesh.vertexCount], numpy.int32).tostring())
						s = mesh.vertexes.tostring()
						f.write(s)
						hash.update(s)
					pos = obj.getPosition() * 1000
					pos += numpy.array(profile.getMachineCenterCoords()) * 1000
					commandList += ['-m', ','.join(map(str, obj._matrix.getA().flatten()))]
					commandList += ['-s', 'posx=%d' % int(pos[0]), '-s', 'posy=%d' % int(pos[1])]
					commandList += ['#' * len(obj._meshList)]
					self._objCount += 1
			self._modelHash = hash.hexdigest()
		if self._objCount > 0:
			self._thread = threading.Thread(target=self._watchProcess, args=(commandList, self._thread))
			self._thread.daemon = True
			self._thread.start()

	def _watchProcess(self, commandList, oldThread):
		if oldThread is not None:
			if self._process is not None:
				self._process.terminate()
			oldThread.join()
		self._id += 1
		self._callback(-1.0, False)
		try:
			self._process = self._runSliceProcess(commandList)
		except OSError:
			traceback.print_exc()
			return
		if self._thread != threading.currentThread():
			self._process.terminate()
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
				if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
					radius = profile.getProfileSettingFloat('filament_diameter') / 2.0
					self._filamentMM /= (math.pi * radius * radius)
			else:
				self._sliceLog.append(line.strip())
			line = self._process.stdout.readline()
		for line in self._process.stderr:
			self._sliceLog.append(line.strip())
		returnCode = self._process.wait()
		try:
			if returnCode == 0:
				pluginError = profile.runPostProcessingPlugins(self._exportFilename)
				if pluginError is not None:
					print pluginError
					self._sliceLog.append(pluginError)
				self._callback(1.0, True)
			else:
				for line in self._sliceLog:
					print line
				self._callback(-1.0, False)
		except:
			pass
		self._process = None

	def _engineSettings(self, extruderCount):
		settings = {
			'layerThickness': int(profile.getProfileSettingFloat('layer_height') * 1000),
			'initialLayerThickness': int(profile.getProfileSettingFloat('bottom_thickness') * 1000) if profile.getProfileSettingFloat('bottom_thickness') > 0.0 else int(profile.getProfileSettingFloat('layer_height') * 1000),
			'filamentDiameter': int(profile.getProfileSettingFloat('filament_diameter') * 1000),
			'filamentFlow': int(profile.getProfileSettingFloat('filament_flow')),
			'extrusionWidth': int(profile.calculateEdgeWidth() * 1000),
			'insetCount': int(profile.calculateLineCount()),
			'downSkinCount': int(profile.calculateSolidLayerCount()) if profile.getProfileSetting('solid_bottom') == 'True' else 0,
			'upSkinCount': int(profile.calculateSolidLayerCount()) if profile.getProfileSetting('solid_top') == 'True' else 0,
			'infillOverlap': int(profile.getProfileSettingFloat('fill_overlap')),
			'initialSpeedupLayers': int(4),
			'initialLayerSpeed': int(profile.getProfileSettingFloat('bottom_layer_speed')),
			'printSpeed': int(profile.getProfileSettingFloat('print_speed')),
			'infillSpeed': int(profile.getProfileSettingFloat('infill_speed')) if int(profile.getProfileSettingFloat('infill_speed')) > 0 else int(profile.getProfileSettingFloat('print_speed')),
			'moveSpeed': int(profile.getProfileSettingFloat('travel_speed')),
			'fanOnLayerNr': int(profile.getProfileSettingFloat('fan_layer')),
			'fanSpeedMin': int(profile.getProfileSettingFloat('fan_speed')) if profile.getProfileSetting('fan_enabled') == 'True' else 0,
			'fanSpeedMax': int(profile.getProfileSettingFloat('fan_speed_max')) if profile.getProfileSetting('fan_enabled') == 'True' else 0,
			'supportAngle': int(-1) if profile.getProfileSetting('support') == 'None' else int(60),
			'supportEverywhere': int(1) if profile.getProfileSetting('support') == 'Everywhere' else int(0),
			'supportLineDistance': int(100 * profile.calculateEdgeWidth() * 1000 / profile.getProfileSettingFloat('support_fill_rate')) if profile.getProfileSettingFloat('support_fill_rate') > 0 else -1,
			'supportXYDistance': int(1000 * profile.getProfileSettingFloat('support_xy_distance')),
			'supportZDistance': int(1000 * profile.getProfileSettingFloat('support_z_distance')),
			'supportExtruder': 0 if profile.getProfileSetting('support_dual_extrusion') == 'First extruder' else (1 if profile.getProfileSetting('support_dual_extrusion') == 'Second extruder' else -1),
			'retractionAmount': int(profile.getProfileSettingFloat('retraction_amount') * 1000) if profile.getProfileSetting('retraction_enable') == 'True' else 0,
			'retractionSpeed': int(profile.getProfileSettingFloat('retraction_speed')),
			'retractionMinimalDistance': int(profile.getProfileSettingFloat('retraction_min_travel') * 1000),
			'retractionAmountExtruderSwitch': int(profile.getProfileSettingFloat('retraction_dual_amount') * 1000),
			'minimalExtrusionBeforeRetraction': int(profile.getProfileSettingFloat('retraction_minimal_extrusion') * 1000),
			'enableCombing': 1 if profile.getProfileSetting('retraction_combing') == 'True' else 0,
			'multiVolumeOverlap': int(profile.getProfileSettingFloat('overlap_dual') * 1000),
			'objectSink': int(profile.getProfileSettingFloat('object_sink') * 1000),
			'minimalLayerTime': int(profile.getProfileSettingFloat('cool_min_layer_time')),
			'minimalFeedrate': int(profile.getProfileSettingFloat('cool_min_feedrate')),
			'coolHeadLift': 1 if profile.getProfileSetting('cool_head_lift') == 'True' else 0,
			'startCode': profile.getAlterationFileContents('start.gcode', extruderCount),
			'endCode': profile.getAlterationFileContents('end.gcode', extruderCount),

			'extruderOffset[1].X': int(profile.getMachineSettingFloat('extruder_offset_x1') * 1000),
			'extruderOffset[1].Y': int(profile.getMachineSettingFloat('extruder_offset_y1') * 1000),
			'extruderOffset[2].X': int(profile.getMachineSettingFloat('extruder_offset_x2') * 1000),
			'extruderOffset[2].Y': int(profile.getMachineSettingFloat('extruder_offset_y2') * 1000),
			'extruderOffset[3].X': int(profile.getMachineSettingFloat('extruder_offset_x3') * 1000),
			'extruderOffset[3].Y': int(profile.getMachineSettingFloat('extruder_offset_y3') * 1000),
			'fixHorrible': 0,
		}
		if profile.getProfileSettingFloat('fill_density') == 0:
			settings['sparseInfillLineDistance'] = -1
		elif profile.getProfileSettingFloat('fill_density') == 100:
			settings['sparseInfillLineDistance'] = settings['extrusionWidth']
			#Set the up/down skins height to 10000 if we want a 100% filled object.
			# This gives better results then normal 100% infill as the sparse and up/down skin have some overlap.
			settings['downSkinCount'] = 10000
			settings['upSkinCount'] = 10000
		else:
			settings['sparseInfillLineDistance'] = int(100 * profile.calculateEdgeWidth() * 1000 / profile.getProfileSettingFloat('fill_density'))
		if profile.getProfileSetting('platform_adhesion') == 'Brim':
			settings['skirtDistance'] = 0
			settings['skirtLineCount'] = int(profile.getProfileSettingFloat('brim_line_count'))
		elif profile.getProfileSetting('platform_adhesion') == 'Raft':
			settings['skirtDistance'] = 0
			settings['skirtLineCount'] = 0
			settings['raftMargin'] = int(profile.getProfileSettingFloat('raft_margin') * 1000)
			settings['raftLineSpacing'] = int(profile.getProfileSettingFloat('raft_line_spacing') * 1000)
			settings['raftBaseThickness'] = int(profile.getProfileSettingFloat('raft_base_thickness') * 1000)
			settings['raftBaseLinewidth'] = int(profile.getProfileSettingFloat('raft_base_linewidth') * 1000)
			settings['raftInterfaceThickness'] = int(profile.getProfileSettingFloat('raft_interface_thickness') * 1000)
			settings['raftInterfaceLinewidth'] = int(profile.getProfileSettingFloat('raft_interface_linewidth') * 1000)
		else:
			settings['skirtDistance'] = int(profile.getProfileSettingFloat('skirt_gap') * 1000)
			settings['skirtLineCount'] = int(profile.getProfileSettingFloat('skirt_line_count'))
			settings['skirtMinLength'] = int(profile.getProfileSettingFloat('skirt_minimal_length') * 1000)

		if profile.getProfileSetting('fix_horrible_union_all_type_a') == 'True':
			settings['fixHorrible'] |= 0x01
		if profile.getProfileSetting('fix_horrible_union_all_type_b') == 'True':
			settings['fixHorrible'] |= 0x02
		if profile.getProfileSetting('fix_horrible_use_open_bits') == 'True':
			settings['fixHorrible'] |= 0x10
		if profile.getProfileSetting('fix_horrible_extensive_stitching') == 'True':
			settings['fixHorrible'] |= 0x04

		if settings['layerThickness'] <= 0:
			settings['layerThickness'] = 1000
		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			settings['gcodeFlavor'] = 1
		return settings

	def _runSliceProcess(self, cmdList):
		kwargs = {}
		if subprocess.mswindows:
			su = subprocess.STARTUPINFO()
			su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			su.wShowWindow = subprocess.SW_HIDE
			kwargs['startupinfo'] = su
			kwargs['creationflags'] = 0x00004000 #BELOW_NORMAL_PRIORITY_CLASS
		return subprocess.Popen(cmdList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)

	def submitSliceInfoOnline(self):
		if profile.getPreference('submit_slice_information') != 'True':
			return
		if version.isDevVersion():
			return
		data = {
			'processor': platform.processor(),
			'machine': platform.machine(),
			'platform': platform.platform(),
			'profile': profile.getProfileString(),
			'preferences': profile.getPreferencesString(),
			'modelhash': self._modelHash,
			'version': version.getVersion(),
		}
		try:
			f = urllib2.urlopen("http://www.youmagine.com/curastats/", data = urllib.urlencode(data), timeout = 1)
			f.read()
			f.close()
		except:
			pass
