from __future__ import absolute_import

from optparse import OptionParser
import sys
import re
import os
import urllib
import urllib2
import platform
import hashlib
import subprocess

if not hasattr(sys, 'frozen'):
	cura_sf_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./cura_sf/"))
	if cura_sf_path not in sys.path:
		sys.path.append(cura_sf_path)

from Cura.util import profile
from Cura.util import version
from Cura.slice.cura_sf.skeinforge_application.skeinforge_plugins.craft_plugins import export

def fixUTF8(input):
	if input.startswith('#UTF8#'):
		return input[6:].decode('utf-8')
	return input

def main():
	parser = OptionParser(usage="usage: %prog [options] <X,Y> <filename>[, <X,Y> <filename>][, ...]")
	parser.add_option("-p", "--profile", action="store", type="string", dest="profile",
					  help="Encoded profile to use for the print")
	parser.add_option("-o", "--output", action="store", type="string", dest="output",
					  help="Output filename")
	(options, args) = parser.parse_args()
	if options.output is None:
		print 'Missing output filename'
		sys.exit(1)
	if options.profile is not None:
		profile.loadGlobalProfileFromString(options.profile)
	options.output = fixUTF8(options.output)

	steamEngineFilename = os.path.join(os.path.dirname(__file__), 'SteamEngine')
	if platform.system() == "Windows":
		steamEngineFilename += ".exe"
		if os.path.isfile("C:\Software\Cura_SteamEngine\_bin\Release\Cura_SteamEngine.exe"):
			steamEngineFilename = "C:\Software\Cura_SteamEngine\_bin\Release\Cura_SteamEngine.exe"
	if os.path.isfile(steamEngineFilename):
		for idx in xrange(0, len(args), 2):
			position = map(float, args[idx].split(','))
			if len(position) < 9 + 2:
				position = position[0:2]
				position += [1,0,0]
				position += [0,1,0]
				position += [0,0,1]

			settings = {}
			settings['layerThickness'] = int(profile.getProfileSettingFloat('layer_height') * 1000)
			settings['initialLayerThickness'] = int(profile.getProfileSettingFloat('bottom_thickness') * 1000)
			settings['filamentDiameter'] = int(profile.getProfileSettingFloat('filament_diameter') * 1000)
			settings['extrusionWidth'] = int(profile.calculateEdgeWidth() * 1000)
			settings['insetCount'] = int(profile.calculateLineCount())
			settings['downSkinCount'] = int(profile.calculateSolidLayerCount())
			settings['upSkinCount'] = int(profile.calculateSolidLayerCount())
			if profile.getProfileSettingFloat('fill_density') > 0:
				settings['sparseInfillLineDistance'] = int(100 * 1000 * profile.calculateEdgeWidth() / profile.getProfileSettingFloat('fill_density'))
			else:
				settings['sparseInfillLineDistance'] = 9999999
			settings['skirtDistance'] = int(profile.getProfileSettingFloat('skirt_gap') * 1000)
			settings['skirtLineCount'] = int(profile.getProfileSettingFloat('skirt_line_count'))

			settings['initialSpeedupLayers'] = int(4)
			settings['initialLayerSpeed'] = int(profile.getProfileSettingFloat('bottom_layer_speed'))
			settings['printSpeed'] = int(profile.getProfileSettingFloat('print_speed'))
			settings['moveSpeed'] = int(profile.getProfileSettingFloat('travel_speed'))
			settings['fanOnLayerNr'] = int(profile.getProfileSettingFloat('fan_layer'))

			cmdList = [steamEngineFilename, args[idx+1], '-o', options.output, '-m', ','.join(map(str, position[2:]))]
			for (key, value) in settings.items():
				cmdList += ['-s', str(key) + "=" + str(value)]
			kwargs = {}
			if subprocess.mswindows:
				su = subprocess.STARTUPINFO()
				su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
				su.wShowWindow = subprocess.SW_HIDE
				kwargs['startupinfo'] = su
			p = subprocess.Popen(cmdList, **kwargs)
			p.communicate()
		return

	clearZ = 0
	resultFile = open(options.output, "w")
	for idx in xrange(0, len(args), 2):
		position = map(float, args[idx].split(','))
		if len(position) < 9 + 2:
			position = position[0:2]
			position += [1,0,0]
			position += [0,1,0]
			position += [0,0,1]
		filenames = fixUTF8(args[idx + 1]).split('|')

		profile.setTempOverride('object_center_x', position[0])
		profile.setTempOverride('object_center_y', position[1])
		if idx == 0:
			resultFile.write(';TYPE:CUSTOM\n')
			resultFile.write(profile.getAlterationFileContents('start.gcode', len(filenames)).replace('?filename?', ' '.join(filenames).encode('ascii', 'replace')))
		else:
			resultFile.write(';TYPE:CUSTOM\n')
			n = output[-1].rfind('Z')+1
			zString = output[-1][n:n+20]
			zString = zString[0:zString.find(' ')]
			clearZ = max(clearZ, float(zString) + 10)
			profile.setTempOverride('clear_z', clearZ)
			print position
			print profile.getAlterationFileContents('nextobject.gcode')
			resultFile.write(profile.getAlterationFileContents('nextobject.gcode').replace('?filename?', ' '.join(filenames).encode('ascii', 'replace')))

		output = []
		for filename in filenames:
			extruderNr = filenames.index(filename)
			profile.resetTempOverride()
			if extruderNr > 0:
				profile.setTempOverride('object_center_x', position[0] - profile.getPreferenceFloat('extruder_offset_x%d' % (extruderNr)))
				profile.setTempOverride('object_center_y', position[1] - profile.getPreferenceFloat('extruder_offset_y%d' % (extruderNr)))
				profile.setTempOverride('fan_enabled', 'False')
				profile.setTempOverride('skirt_line_count', '0')
				profile.setTempOverride('alternative_center', filenames[0])
			else:
				profile.setTempOverride('object_center_x', position[0])
				profile.setTempOverride('object_center_y', position[1])
			profile.setTempOverride('object_matrix', ','.join(map(str, position[2:11])))
			output.append(export.getOutput(filename))
			profile.resetTempOverride()
		if len(output) == 1:
			resultFile.write(output[0])
		else:
			stitchMultiExtruder(output, resultFile)
	resultFile.write(';TYPE:CUSTOM\n')
	resultFile.write(profile.getAlterationFileContents('end.gcode'))
	resultFile.close()

	print "Running plugins"
	ret = profile.runPostProcessingPlugins(options.output)
	if ret is not None:
		print ret
	print "Finalizing %s" % (os.path.basename(options.output))
	if profile.getPreference('submit_slice_information') == 'True':
		filenames = fixUTF8(args[idx + 1]).split('|')
		for filename in filenames:
			m = hashlib.sha512()
			f = open(filename, "rb")
			while True:
				chunk = f.read(1024)
				if not chunk:
					break
				m.update(chunk)
			f.close()
			data = {
				'processor': platform.processor(),
				'machine': platform.machine(),
				'platform': platform.platform(),
				'profile': profile.getGlobalProfileString(),
				'preferences': profile.getGlobalPreferencesString(),
				'modelhash': m.hexdigest(),
				'version': version.getVersion(),
			}
			try:
				f = urllib2.urlopen("http://platform.ultimaker.com/curastats/", data = urllib.urlencode(data), timeout = 5);
				f.read()
				f.close()
			except:
				pass


def stitchMultiExtruder(outputList, resultFile):
	print "Stitching %i files for multi-extrusion" % (len(outputList))
	currentExtruder = 0
	resultFile.write('T%d\n' % (currentExtruder))
	layerNr = -1
	hasLine = True
	outputList = map(lambda o: o.split('\n'), outputList)
	outputOrder = range(0, len(outputList))
	while hasLine:
		hasLine = False
		outputOrder.reverse()
		for outputIdx in outputOrder:
			layerHasLine = False
			while len(outputList[outputIdx]) > 0:
				line = outputList[outputIdx].pop(0)
				hasLine = True
				if line.startswith(';LAYER:'):
					break
				if 'Z' in line:
					lastZ = float(re.search('Z([^\s]+)', line).group(1))
				if not layerHasLine:
					nextExtruder = outputIdx
					resultFile.write(';LAYER:%d\n' % (layerNr))
					resultFile.write(';EXTRUDER:%d\n' % (nextExtruder))
					if nextExtruder != currentExtruder:
						resultFile.write(';TYPE:CUSTOM\n')
						profile.setTempOverride('extruder', nextExtruder)
						resultFile.write(profile.getAlterationFileContents('switchExtruder.gcode') + '\n')
						profile.resetTempOverride()
						currentExtruder = nextExtruder
					layerHasLine = True
				resultFile.write(line)
				resultFile.write('\n')
		layerNr += 1

if __name__ == '__main__':
	main()
