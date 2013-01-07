from __future__ import absolute_import

import platform
import os
import subprocess
import sys

from Cura.util import resources
from Cura.util import profile

#How long does each step take compared to the others. This is used to make a better scaled progress bar, and guess time left.
sliceStepTimeFactor = {
	'start': 3.3713991642,
	'slice': 15.4984838963,
	'preface': 5.17178297043,
	'inset': 116.362634182,
	'fill': 215.702672005,
	'multiply': 21.9536788464,
	'speed': 12.759510994,
	'raft': 31.4580039978,
	'skirt': 19.3436040878,
	'skin': 1.0,
	'joris': 1.0,
	'dwindle': 1.0,
	'comb': 23.7805759907,
	'cool': 27.148763895,
	'hop': 1.0,
	'dimension': 90.4914340973
}

totalRunTimeFactor = 0
for v in sliceStepTimeFactor.values():
	totalRunTimeFactor += v

def getPyPyExe():
	"Return the path to the pypy executable if we can find it. Else return False"
	if platform.system() == "Windows":
		exeName = "pypy.exe"
		pypyExe = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../pypy/pypy.exe"))
	else:
		exeName = "pypy"
		if hasattr(sys, 'frozen'):
			pypyExe = os.path.normpath(os.path.join(resources.resourceBasePath, "pypy/bin/pypy"))
		else:
			pypyExe = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../pypy/bin/pypy"))
	if os.path.exists(pypyExe):
		return pypyExe

	path = os.environ['PATH']
	paths = path.split(os.pathsep)
	for p in paths:
		pypyExe = os.path.join(p, exeName)
		if os.path.exists(pypyExe):
			return pypyExe 
	return None

def getExportFilename(filename, ext = "gcode"):
	return "%s.%s" % (filename[: filename.rfind('.')], ext)

#Get a short filename in 8.3 format for proper saving on SD.
def getShortFilename(filename):
	ext = filename[filename.rfind('.'):]
	filename = filename[: filename.rfind('.')]
	return filename[:8] + ext[:2]

def getSliceCommand(outputfilename, filenames, positions):
	pypyExe = getPyPyExe()
	if pypyExe is None:
		pypyExe = sys.executable
	cmd = [pypyExe, '-m', 'Cura.slice', '-p', profile.getGlobalProfileString(), '-o']
	try:
		cmd.append(str(outputfilename))
	except UnicodeEncodeError:
		cmd.append("#UTF8#" + outputfilename.encode("utf-8"))
	for idx in xrange(0, len(filenames)):
		filename = filenames[idx]
		position = positions[idx]
		cmd.append(','.join(map(str, position)))
		try:
			cmd.append(str(filename))
		except UnicodeEncodeError:
			cmd.append("#UTF8#" + filename.encode("utf-8"))
	return cmd

def startSliceCommandProcess(cmdList):
	kwargs = {} 
	if subprocess.mswindows: 
		su = subprocess.STARTUPINFO() 
		su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		su.wShowWindow = subprocess.SW_HIDE
		kwargs['startupinfo'] = su
	return subprocess.Popen(cmdList, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
