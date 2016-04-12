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
import re

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
		self._printProgress = 0
		self._ZPosition = 0
		self._pausePosition = None

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
		self._ZPosition = 0
		self._pausePosition = None

	def coolDown(self):
		self.sendCommand("M108") #Cancel heatup
		cooldown_toolhead = "M104 S0"
		for i in range(0, int(profile.getMachineSetting('extruder_amount'))):
			change_toolhead = "T{}".format(i)
			self.sendCommand(change_toolhead)
			self.sendCommand(cooldown_toolhead)
		self.sendCommand("M140 S0") #Bed

	def disableSteppers(self):
		self.sendCommand("M18")

	def setLCDmessage(self):
		cancel_text = "Print canceled"
		formatted_command = "M117 {}".format(cancel_text)
		self.sendCommand(formatted_command)

	#Abort the previously loaded print file
	def cancelPrint(self):
		if (not self.isPrinting() and not self.isPaused()) or \
			self._process is None:
			return
		self._process.stdin.write('STOP\n')
		self._printProgress = 0
		self._ZPosition = 0
		self._pausePosition = None
		self.coolDown()
		self.disableSteppers()
		self.setLCDmessage()

	def isPrinting(self):
		return self._commState == machineCom.MachineCom.STATE_PRINTING

	#Returns true if we have the ability to pause the file printing.
	def hasPause(self):
		return True

	def isPaused(self):
		return self._commState == machineCom.MachineCom.STATE_PAUSED

	#Pause or unpause the printing depending on the value, if supported.
	def pause(self, value):
		if not (self.isPrinting() or self.isPaused()) or self._process is None:
			return
		if value:
			start_gcode = profile.getAlterationFileContents('start.gcode')
			start_gcode_lines = len(start_gcode.split("\n"))
			parkX = profile.getMachineSettingFloat('machine_width') - 10
			parkY = profile.getMachineSettingFloat('machine_depth') - 10
			maxZ = profile.getMachineSettingFloat('machine_height') - 10
			#retract_amount = profile.getProfileSettingFloat('retraction_amount')
			retract_amount = 5.0
			moveZ = 10.0

			self._process.stdin.write("PAUSE\n")
			if self._printProgress - 5 > start_gcode_lines: # Substract 5 because of the marlin queue
				x = None
				y = None
				e = None
				f = None
				for i in xrange(self._printProgress - 1, start_gcode_lines, -1):
					line = self._gcodeData[i]
					if ('G0' in line or 'G1' in line) and 'X' in line and x is None:
						x = float(re.search('X(-?[0-9\.]*)', line).group(1))
					if ('G0' in line or 'G1' in line) and 'Y' in line and y is None:
						y = float(re.search('Y(-?[0-9\.]*)', line).group(1))
					if ('G0' in line or 'G1' in line) and 'E' in line and e is None:
						e = float(re.search('E(-?[0-9\.]*)', line).group(1))
					if ('G0' in line or 'G1' in line) and 'F' in line and f is None:
						f = int(re.search('F(-?[0-9\.]*)', line).group(1))
					if x is not None and y is not None and f is not None and e is not None:
						break
				if f is None:
					f = 1200

				if x is not None and y is not None:
					# Set E relative positioning
					self.sendCommand("M83")

					# Retract 1mm
					retract = ("E-%f" % retract_amount)

					#Move the toolhead up
					newZ = self._ZPosition + moveZ
					if maxZ < newZ:
						newZ = maxZ

					if newZ > self._ZPosition:
						move = ("Z%f " % (newZ))
					else: #No z movement, too close to max height 
						move = ""
					retract_and_move = "G1 {} {}F120".format(retract, move)
					self.sendCommand(retract_and_move)

					#Move the head away
					self.sendCommand("G1 X%f Y%f F9000" % (parkX, parkY))

					#Disable the E steppers
					self.sendCommand("M84 E0")
					# Set E absolute positioning
					self.sendCommand("M82")

					self._pausePosition = (x, y, self._ZPosition, f, e)
		else:
			if self._pausePosition:
				retract_amount = profile.getProfileSettingFloat('retraction_amount')
				# Set E relative positioning
				self.sendCommand("M83")

				#Prime the nozzle when changing filament
				self.sendCommand("G1 E%f F120" % (retract_amount)) #Push the filament out
				self.sendCommand("G1 E-%f F120" % (retract_amount)) #retract again

				# Position the toolhead to the correct position again
				self.sendCommand("G1 X%f Y%f Z%f F%d" % self._pausePosition[0:4])

				# Prime the nozzle again
				self.sendCommand("G1 E%f F120" % (retract_amount))
				# Set proper feedrate
				self.sendCommand("G1 F%d" % (self._pausePosition[3]))
				# Set E absolute position to cancel out any extrude/retract that occured
				self.sendCommand("G92 E%f" % (self._pausePosition[4]))
				# Set E absolute positioning
				self.sendCommand("M82")
			self._process.stdin.write("RESUME\n")
			self._pausePosition = None

	#Amount of progression of the current print file. 0.0 to 1.0
	def getPrintProgress(self):
		return (self._printProgress, len(self._gcodeData), self._ZPosition)

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
				if len(self._log) > 200:
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
				self._doCallback('')
			elif line[0] == 'progress':
				self._printProgress = int(line[1])
				self._doCallback()
			elif line[0] == 'changeZ':
				self._ZPosition = float(line[1])
				self._doCallback()
			else:
				print line
			line = self._process.stdout.readline()
		self._process = None
