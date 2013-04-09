from __future__ import absolute_import

from optparse import OptionParser
import sys
import re
import os
import urllib
import urllib2
import platform
import hashlib

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
			if extruderNr > 0:
				if profile.getProfileSettingFloat('filament_diameter%d' % (extruderNr + 1)) > 0:
					profile.setTempOverride('filament_diameter', profile.getProfileSetting('filament_diameter%d' % (extruderNr + 1)))
			print extruderNr, profile.getPreferenceFloat('extruder_offset_x%d' % (extruderNr)), profile.getPreferenceFloat('extruder_offset_y%d' % (extruderNr))
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


def isPrintingLine(line):
	if line.startswith("G1") and ('X' in line or 'Y' in line) and 'E' in line:
		return True
	return False

def getCodeFloat(line, code, default):
	n = line.find(code) + 1
	if n < 1:
		return default
	m = line.find(' ', n)
	try:
		if m < 0:
			return float(line[n:])
		return float(line[n:m])
	except:
		return default

def stitchMultiExtruder(outputList, resultFile):
	print "Stitching %i files for multi-extrusion" % (len(outputList))
	currentExtruder = 0
	resultFile.write('T%d\n' % (currentExtruder))
	layerNr = 0
	hasLine = True
	outputList = map(lambda o: o.split('\n'), outputList)
	outputOrder = range(0, len(outputList))
	outputSlice = []
	for n in xrange(0, len(outputList)):
		outputSlice.append([0, 0])
	currentX = 0
	currentY = 0
	currentZ = 0
	currentF = 60
	while hasLine:
		hasLine = layerNr < 1000
		for n in xrange(0, len(outputList)):
			outputSlice[n][0] = outputSlice[n][1] + 1
			outputSlice[n][1] = outputSlice[n][0]
			while outputSlice[n][1] < len(outputList[n]) and not outputList[n][outputSlice[n][1]].startswith(';LAYER:'):
				outputSlice[n][1] += 1
		outputOrder = range(currentExtruder, len(outputList)) + range(0, currentExtruder)
		for n in outputOrder:
			if outputSlice[n][1] > outputSlice[n][0] + 1:
				nextExtruder = n
				resultFile.write(';LAYER:%d\n' % (layerNr))
				resultFile.write(';EXTRUDER:%d\n' % (nextExtruder))

				startSlice = outputSlice[n][0]
				endSlice = outputSlice[n][1]

				currentE = 0
				while startSlice < len(outputList[n]) and not isPrintingLine(outputList[n][startSlice]):
					currentE = getCodeFloat(outputList[n][startSlice], 'E', currentE)
					currentX = getCodeFloat(outputList[n][startSlice], 'X', currentX)
					currentY = getCodeFloat(outputList[n][startSlice], 'Y', currentY)
					currentZ = getCodeFloat(outputList[n][startSlice], 'Z', currentZ)
					currentF = getCodeFloat(outputList[n][startSlice], 'F', currentF)
					startSlice += 1
				while not isPrintingLine(outputList[n][endSlice-1]):
					endSlice -= 1

				if nextExtruder != currentExtruder:
					profile.setTempOverride('extruder', nextExtruder)
					profile.setTempOverride('new_x', currentX)
					profile.setTempOverride('new_y', currentY)
					profile.setTempOverride('new_z', currentZ)
					resultFile.write(profile.getAlterationFileContents('switchExtruder.gcode') + '\n')
					profile.resetTempOverride()
					currentExtruder = nextExtruder

				for idx in xrange(outputSlice[n][0], startSlice):
					if not 'G1' in outputList[n][idx]:
						resultFile.write(outputList[n][idx])
						resultFile.write('\n')

				resultFile.write('G1 X%f Y%f Z%f F%f\n' % (currentX, currentY, currentZ, profile.getProfileSettingFloat('travel_speed') * 60))
				resultFile.write('G1 F%f\n' % (currentF))
				resultFile.write('G92 E%f\n' % (currentE))
				for idx in xrange(startSlice, endSlice):
					resultFile.write(outputList[n][idx])
					resultFile.write('\n')
					currentX = getCodeFloat(outputList[n][idx], 'X', currentX)
					currentY = getCodeFloat(outputList[n][idx], 'Y', currentY)
					currentZ = getCodeFloat(outputList[n][idx], 'Z', currentZ)
					hasLine = True
				resultFile.write('G92 E0\n')
		layerNr += 1

if __name__ == '__main__':
	main()
