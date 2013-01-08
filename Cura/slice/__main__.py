from __future__ import absolute_import

from optparse import OptionParser
import sys
import re

from Cura.util import profile
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

	resultFile = open(options.output, "w")
	for idx in xrange(0, len(args), 2):
		position = map(float, args[0].split(','))
		if len(position) < 9 + 2:
			position = position[0:2]
			position += [1,0,0]
			position += [0,1,0]
			position += [0,0,1]
		filenames = fixUTF8(args[idx + 1]).split('|')

		if idx == 0:
			resultFile.write(';TYPE:CUSTOM\n')
			resultFile.write(profile.getAlterationFileContents('start.gcode').replace('?filename?', ' '.join(filenames).encode('ascii', 'replace')))
		else:
			resultFile.write(';TYPE:CUSTOM\n')
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
