"""
The dummy connection is a virtual printer connection which simulates the connection to a printer without doing anything.
This is only enabled when you have a development version. And is used for debugging.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import threading
import json
import httplib as httpclient
import urllib
import time

from Cura.util.printerConnection import printerConnectionBase

class dummyConnectionGroup(printerConnectionBase.printerConnectionGroup):
	"""
	Group used for dummy conections. Always shows 2 dummy connections for debugging.
	Has a very low priority so it does not prevent other connections from taking priority.
	"""
	def __init__(self):
		super(dummyConnectionGroup, self).__init__("Dummy")
		self._list = [dummyConnection("Dummy 1"), dummyConnection("Dummy 2")]

	def getAvailableConnections(self):
		return self._list

	def getIconID(self):
		return 5

	def getPriority(self):
		return -100

class dummyConnection(printerConnectionBase.printerConnectionBase):
	"""
	A dummy printer class to debug printer windows.
	"""
	def __init__(self, name):
		super(dummyConnection, self).__init__(name)

		self._printing = False
		self._lineCount = 0
		self._progressLine = 0

		self.printThread = threading.Thread(target=self._dummyThread)
		self.printThread.daemon = True
		self.printThread.start()

	#Load the data into memory for printing, returns True on success
	def loadGCodeData(self, dataStream):
		if self._printing:
			return False
		self._lineCount = 0
		for line in dataStream:
			#Strip out comments, we do not need to send comments
			if ';' in line:
				line = line[:line.index(';')]
			#Strip out whitespace at the beginning/end this saves data to send.
			line = line.strip()

			if len(line) < 1:
				continue
			self._lineCount += 1
		self._doCallback()
		return True

	#Start printing the previously loaded file
	def startPrint(self):
		print 'startPrint', self._printing, self._lineCount
		if self._printing or self._lineCount < 1:
			return
		self._progressLine = 0
		self._printing = True

	#Abort the previously loaded print file
	def cancelPrint(self):
		self._printing = False

	def isPrinting(self):
		return self._printing

	#Amount of progression of the current print file. 0.0 to 1.0
	def getPrintProgress(self):
		if self._lineCount < 1:
			return 0.0
		return float(self._progressLine) / float(self._lineCount)

	# Return if the printer with this connection type is available
	def isAvailable(self):
		return True

	# Get the connection status string. This is displayed to the user and can be used to communicate
	#  various information to the user.
	def getStatusString(self):
		return "DUMMY!:%i %i:%i" % (self._progressLine, self._lineCount, self._printing)

	def _dummyThread(self):
		while True:
			if not self._printing:
				time.sleep(5)
				self._doCallback()
			else:
				time.sleep(0.01)
				self._progressLine += 1
				if self._progressLine == self._lineCount:
					self._printing = False
				self._doCallback()
