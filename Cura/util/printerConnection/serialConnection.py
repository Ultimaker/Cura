"""
The serial/USB printer connection. Uses a 2nd python process to connect to the printer so we never
have locking problems where other threads in python can block the USB printing.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import threading
import time
import platform
import os
import sys
import subprocess
import json

from Cura.util import profile
from Cura.util import machineCom
from Cura.util.printerConnection import printerConnectionBase

class serialConnectionGroup(printerConnectionBase.printerConnectionGroup):
	"""
	The serial connection group. Keeps track of all available serial ports,
	and builds a serialConnection for each port.
	"""
	def __init__(self):
		super(serialConnectionGroup, self).__init__("USB")
		self._connectionMap = {}

	def getAvailableConnections(self):
		if profile.getMachineSetting('serial_port') == 'AUTO':
			serialList = machineCom.serialList(True)
		else:
			serialList = [profile.getMachineSetting('serial_port')]
		for port in serialList:
			if port not in self._connectionMap:
				self._connectionMap[port] = serialConnection(port)
		for key in self._connectionMap.keys():
			if key not in serialList and not self._connectionMap[key].isActiveConnectionOpen():
				self._connectionMap.pop(key)
		return self._connectionMap.values()

	def getIconID(self):
		return 6

	def getPriority(self):
		return 50

class serialConnection(printerConnectionBase.printerConnectionBase):
	"""
	A serial connection. Needs to build an active-connection.
	When an active connection is created, a 2nd python process is spawned which handles the actual serial communication.

	This class communicates with the Cura.serialCommunication module trough stdin/stdout pipes.
	"""
	def __init__(self, port):
		super(serialConnection, self).__init__(port)
		self._portName = port

		self._process = None
		self._thread = None

		self._temperature = []
		self._targetTemperature = []
		self._bedTemperature = 0
		self._targetBedTemperature = 0
		self._log = []

		self._commState = None
		self._commStateString = None
		self._gcodeData = []

	#Load the data into memory for printing, returns True on success
	def loadGCodeData(self, dataStream):
		if self.isPrinting() is None:
			return False
		self._gcodeData = []
		for line in dataStream:
			#Strip out comments, we do not need to send comments
			if ';' in line:
				line = line[:line.index(';')]
			#Strip out whitespace at the beginning/end this saves data to send.
			line = line.strip()

			if len(line) < 1:
				continue
			self._gcodeData.append(line)
		return True

	#Start printing the previously loaded file
	def startPrint(self):
		if self.isPrinting() or len(self._gcodeData) < 1 or self._process is None:
			return
		self._process.stdin.write('STOP\n')
		for line in self._gcodeData:
			self._process.stdin.write('G:%s\n' % (line))
		self._process.stdin.write('START\n')
		self._printProgress = 0

	#Abort the previously loaded print file
	def cancelPrint(self):
		if not self.isPrinting()or self._process is None:
			return
		self._process.stdin.write('STOP\n')
		self._printProgress = 0

	def isPrinting(self):
		return self._commState == machineCom.MachineCom.STATE_PRINTING

	#Amount of progression of the current print file. 0.0 to 1.0
	def getPrintProgress(self):
		if len(self._gcodeData) < 1:
			return 0.0
		return float(self._printProgress) / float(len(self._gcodeData))

	# Return if the printer with this connection type is available
	def isAvailable(self):
		return True

	# Get the connection status string. This is displayed to the user and can be used to communicate
	#  various information to the user.
	def getStatusString(self):
		return "%s" % (self._commStateString)

	#Returns true if we need to establish an active connection. True for serial connections.
	def hasActiveConnection(self):
		return True

	#Open the active connection to the printer so we can send commands
	def openActiveConnection(self):
		self.closeActiveConnection()
		self._thread = threading.Thread(target=self._serialCommunicationThread)
		self._thread.daemon = True
		self._thread.start()

	#Close the active connection to the printer
	def closeActiveConnection(self):
		if self._process is not None:
			self._process.terminate()
			self._thread.join()

	#Is the active connection open right now.
	def isActiveConnectionOpen(self):
		if self._process is None:
			return False
		return self._commState == machineCom.MachineCom.STATE_OPERATIONAL or self._commState == machineCom.MachineCom.STATE_PRINTING or self._commState == machineCom.MachineCom.STATE_PAUSED

	#Are we trying to open an active connection right now.
	def isActiveConnectionOpening(self):
		if self._process is None:
			return False
		return self._commState == machineCom.MachineCom.STATE_OPEN_SERIAL or self._commState == machineCom.MachineCom.STATE_CONNECTING or self._commState == machineCom.MachineCom.STATE_DETECT_SERIAL or self._commState == machineCom.MachineCom.STATE_DETECT_BAUDRATE

	def getTemperature(self, extruder):
		if extruder >= len(self._temperature):
			return None
		return self._temperature[extruder]

	def getBedTemperature(self):
		return self._bedTemperature

	#Are we able to send a direct command with sendCommand at this moment in time.
	def isAbleToSendDirectCommand(self):
		return self.isActiveConnectionOpen()

	#Directly send a command to the printer.
	def sendCommand(self, command):
		if self._process is None:
			return
		self._process.stdin.write('C:%s\n' % (command))

	#Returns true if we got some kind of error. The getErrorLog returns all the information to diagnose the problem.
	def isInErrorState(self):
		return self._commState == machineCom.MachineCom.STATE_ERROR or self._commState == machineCom.MachineCom.STATE_CLOSED_WITH_ERROR

	#Returns the error log in case there was an error.
	def getErrorLog(self):
		return '\n'.join(self._log)

	def _serialCommunicationThread(self):
		if platform.system() == "Darwin" and hasattr(sys, 'frozen'):
			cmdList = [os.path.join(os.path.dirname(sys.executable), 'Cura'), '--serialCommunication']
			cmdList += [self._portName + ':' + profile.getMachineSetting('serial_baud')]
		else:
			cmdList = [sys.executable, '-m', 'Cura.serialCommunication']
			cmdList += [self._portName, profile.getMachineSetting('serial_baud')]
		if platform.system() == "Darwin":
			if platform.machine() == 'i386':
				cmdList = ['arch', '-i386'] + cmdList
		self._process = subprocess.Popen(cmdList, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		line = self._process.stdout.readline()
		while len(line) > 0:
			line = line.strip()
			line = line.split(':', 1)
			if line[0] == '':
				pass
			elif line[0] == 'log':
				self._log.append(line[1])
				if len(self._log) > 30:
					self._log.pop(0)
			elif line[0] == 'temp':
				line = line[1].split(':')
				self._temperature = json.loads(line[0])
				self._targetTemperature = json.loads(line[1])
				self._bedTemperature = float(line[2])
				self._targetBedTemperature = float(line[3])
				self._doCallback()
			elif line[0] == 'message':
				self._doCallback(line[1])
			elif line[0] == 'state':
				line = line[1].split(':', 1)
				self._commState = int(line[0])
				self._commStateString = line[1]
				self._doCallback()
			elif line[0] == 'progress':
				self._printProgress = int(line[1])
				self._doCallback()
			else:
				print line
			line = self._process.stdout.readline()
		self._process = None
