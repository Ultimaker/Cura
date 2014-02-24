"""
Serial communication with the printer for printing is done from a separate process,
this to ensure that the PIL does not block the serial printing.

This file is the 2nd process that is started to handle communication with the printer.
And handles all communication with the initial process.
"""

__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"
import sys
import time
import os
import json

from Cura.util import machineCom

class serialComm(object):
	"""
	The serialComm class is the interface class which handles the communication between stdin/stdout and the machineCom class.
	This interface class is used to run the (USB) serial communication in a different process then the GUI.
	"""
	def __init__(self, portName):
		self._comm = None
		self._gcodeList = []

		self._comm = machineCom.MachineCom(portName, callbackObject=self)

	def mcLog(self, message):
		sys.stdout.write('log:%s\n' % (message))

	def mcTempUpdate(self, temp, bedTemp, targetTemp, bedTargetTemp):
		sys.stdout.write('temp:%s:%s:%f:%f\n' % (json.dumps(temp), json.dumps(targetTemp), bedTemp, bedTargetTemp))

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
			elif line[0] == 'C':
				self._comm.sendCommand(line[1])
			elif line[0] == 'START':
				self._comm.printGCode(self._gcodeList)
			else:
				sys.stderr.write(str(line))

def startMonitor(portName):
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
	comm = serialComm(portName)
	comm.monitorStdin()

def main():
	if len(sys.argv) != 2:
		return
	portName = sys.argv[1]
	startMonitor(portName)

if __name__ == '__main__':
	main()
