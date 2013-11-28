__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import threading
import json
import httplib as httpclient
import urllib
import time

from Cura.util.printerConnection import printerConnectionBase

#Dummy printer class which is always
class dummyConnection(printerConnectionBase.printerConnectionBase):
	def __init__(self):
		super(dummyConnection, self).__init__()

		self._printing = False
		self._lineCount = 0
		self._progressLine = 0

		self.printThread = threading.Thread(target=self._dummyThread)
		self.printThread.daemon = True
		self.printThread.start()

	#Load the file into memory for printing.
	def loadFile(self, filename):
		if self._printing:
			return
		self._lineCount = 0
		f = open(filename, "r")
		for line in f:
			#Strip out comments, we do not need to send comments
			if ';' in line:
				line = line[:line.index(';')]
			#Strip out whitespace at the beginning/end this saves data to send.
			line = line.strip()

			if len(line) < 1:
				continue
			self._lineCount += 1

	#Start printing the previously loaded file
	def startPrint(self):
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
		return "DUMMY!"

	def _dummyThread(self):
		while True:
			if not self._printing:
				time.sleep(5)
			else:
				time.sleep(0.01)
				self._progressLine += 1
				if self._progressLine == self._lineCount:
					self._printing = False
				self._doCallback()
