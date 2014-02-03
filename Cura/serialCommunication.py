__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

# Serial communication with the printer for printing is done from a separate process,
# this to ensure that the PIL does not block the serial printing.

import sys
import time
import os
import json

from Cura.util import machineCom

class serialComm(object):
	def __init__(self, portName):
		self._comm = None
		self._gcodeList = []

		self._comm = machineCom.MachineCom(portName, callbackObject=self)

	def mcLog(self, message):
		sys.stdout.write('log:%s\n' % (message))

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		sys.stdout.write('temp:%s\n' % json.dumps(temp))

	def mcStateChange(self, state):
		if self._comm is None:
			return
		sys.stdout.write('state:%d:%s\n' % (state, self._comm.getStateString()))

	def mcMessage(self, message):
		sys.stdout.write('message:%s\n' % (message))

	def mcProgress(self, lineNr):
		sys.stdout.write('progress:%d\n' % (lineNr))

	def mcZChange(self, newZ):
		sys.stdout.write('changeZ:%d\n' % (newZ))

	def monitorStdin(self):
		while not self._comm.isClosed():
			line = sys.stdin.readline().strip()
			line = line.split(':', 1)
			if line[0] == 'STOP':
				self._comm.cancelPrint()
				self._gcodeList = ['M110']
			elif line[0] == 'G':
				self._gcodeList.append(line[1])
			elif line[0] == 'START':
				self._comm.printGCode(self._gcodeList)
			else:
				sys.stderr.write(str(line))

def main():
	if len(sys.argv) != 2:
		return
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
	portName = sys.argv[1]
	comm = serialComm(portName)
	comm.monitorStdin()

if __name__ == '__main__':
	main()
