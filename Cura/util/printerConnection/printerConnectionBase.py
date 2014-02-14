"""
Base of all printer connections. A printer connection is a way a connection can be made with a printer.
The connections are based on a group, where each group can have 1 or more connections.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import traceback

class printerConnectionGroup(object):
	"""
	Base for the printer connection group, needs to be subclassed.
	Has functions for all available connections, getting the name, icon and priority.

	The getIconID, getPriority and getAvailableConnections functions should be overloaded in a subclass.
	"""
	def __init__(self, name):
		self._name = name

	def getAvailableConnections(self):
		return []

	def getName(self):
		return self._name

	def getIconID(self):
		return 5

	def getPriority(self):
		return -100

	def __cmp__(self, other):
		return self.getPriority() - other.getPriority()

	def __repr__(self):
		return '%s %d' % (self._name, self.getPriority())

class printerConnectionBase(object):
	"""
	Base class for different printer connection implementations.
		A printer connection can connect to printers in different ways, trough network, USB or carrier pigeons.
		Each printer connection has different capabilities that you can query with the "has" functions.
		Each printer connection has a state that you can query with the "is" functions.
		Each printer connection has callback objects that receive status updates from the printer when information changes.
	"""
	def __init__(self, name):
		self._callbackList = []
		self._name = name
		self.window = None

	def getName(self):
		return self._name

	#Load the data into memory for printing, returns True on success
	def loadGCodeData(self, dataStream):
		return False

	#Start printing the previously loaded file
	def startPrint(self):
		pass

	#Abort the previously loaded print file
	def cancelPrint(self):
		pass

	def isPrinting(self):
		return False

	#Amount of progression of the current print file. 0.0 to 1.0
	def getPrintProgress(self):
		return 0.0

	#Returns true if we need to establish an active connection.
	# Depending on the type of the connection some types do not need an active connection (Doodle3D WiFi Box for example)
	def hasActiveConnection(self):
		return False

	#Open the active connection to the printer so we can send commands
	def openActiveConnection(self):
		pass

	#Close the active connection to the printer
	def closeActiveConnection(self):
		pass

	#Is the active connection open right now.
	def isActiveConnectionOpen(self):
		return False

	#Are we trying to open an active connection right now.
	def isActiveConnectionOpening(self):
		return False

	#Returns true if we have the ability to pause the file printing.
	def hasPause(self):
		return False

	def isPaused(self):
		return False

	#Pause or unpause the printing depending on the value, if supported.
	def pause(self, value):
		pass

	#Are we able to send a direct coammand with sendCommand at this moment in time.
	def isAbleToSendDirectCommand(self):
		return False

	#Directly send a command to the printer.
	def sendCommand(self, command):
		pass

	# Return if the printer with this connection type is available for possible printing right now.
	#  It is used to auto-detect which connection should default to the print button.
	#  This means the printer is detected, but no connection has been made yet.
	#  Example: COM port is detected, but no connection has been made.
	#  Example: WiFi box is detected and is ready to print with a printer connected
	def isAvailable(self):
		return False

	#Get the temperature of an extruder, returns None is no temperature is known for this extruder
	def getTemperature(self, extruder):
		return None

	#Get the temperature of the heated bed, returns None is no temperature is known for the heated bed
	def getBedTemperature(self):
		return None

	# Get the connection status string. This is displayed to the user and can be used to communicate
	#  various information to the user.
	def getStatusString(self):
		return "TODO"

	def addCallback(self, callback):
		self._callbackList.append(callback)

	def removeCallback(self, callback):
		if callback in self._callbackList:
			self._callbackList.remove(callback)

	#Returns true if we got some kind of error. The getErrorLog returns all the information to diagnose the problem.
	def isInErrorState(self):
		return False
	#Returns the error log in case there was an error.
	def getErrorLog(self):
		return ""

	#Run a callback, this can be ran from a different thread, the receivers of the callback need to make sure they are thread safe.
	def _doCallback(self, param=None):
		for callback in self._callbackList:
			try:
				callback(self, param)
			except:
				self.removeCallback(callback)
				traceback.print_exc()
